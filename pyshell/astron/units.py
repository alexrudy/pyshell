# -*- coding: utf-8 -*-
# 
#  units.py
#  pyshell
#  
#  Created by Alexander Rudy on 2013-12-02.
#  Copyright 2013 Alexander Rudy. All rights reserved.
# 

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import numpy as np
import six
import abc
import warnings
import contextlib
from collections import OrderedDict
import astropy.units as u

from ..util import descriptor__get__

u.du = u.dimensionless_unscaled


def ensure_quantity(value, unit, isscalar=None):
    """Ensure that a quantity exists and convert it."""
    quantity = u.Quantity(value, unit=unit)
    if isscalar is None:
        return quantity
    elif quantity.isscalar != isscalar:
        raise ValueError("Quantity {} should{} be scalar!".format(value, "" if isscalar else " not"))
    else:
        return quantity

def unscale_unit(old_unit):
    """Return a unit, scale tuple"""
    new_unit = old_unit / u.Unit(old_unit.scale)
    return (new_unit, old_unit.scale)

def unscale(quantity):
    """Remove the scale on a quantity."""
    old_unit = quantity.unit
    new_unit, scale = unscale_unit(old_unit)
    new_value = quantity.value * scale
    return quantity.__quantity_instance__(new_value,new_unit)
    
def unscaled_unit(unit, bases=None):
    """Unscale a given unit."""
    if bases is not None:
        unit = unit.compose(units=bases, max_depth=4)[0]
    new_unit, scale = unscale_unit(unit)
    return new_unit
    
def recompose(quantity, bases, warn_compositons=False):
    """Recompose a quantity in terms of the given bases."""
    composed = quantity.unit.compose(units=bases, max_depth=4)
    result = quantity.to(composed[0]).copy()
    if len(composed) != 1 and warn_compositons:
        warnings.warn("Multiple compositions: {}".format(composed))
    return unscale(result)

class FrozenError(Exception):
    """An error occuring when trying to set frozen attributes."""
    pass

class UnitsProperty(object):
    """A descriptor which enforces units."""
    def __init__(self, name, unit, nonnegative=False, warn_for_unit_composition=False):
        super(UnitsProperty, self).__init__()
        self.name = name
        self._unit = unit
        self._attr = '_{}_{}'.format(self.__class__.__name__, name.replace(" ", "_"))
        self._nn = nonnegative
        self._warncompositon = warn_for_unit_composition
        
    def bases(self, obj):
        """Return the bases."""
        return getattr(obj, '_bases', None)
        
    def recompose(self, quantity, bases):
        """Recompose a unit into a new base set."""
        return recompose(quantity, bases, self._warncompositon)
        
    def recomposed_unit(self, obj):
        """Get the recomposed unit."""
        return unscaled_unit(self._unit, self.bases(obj))
        
    def __set__(self, obj, value):
        """Set this property's value"""
        return self.set(obj, value)
        
    def set(self, obj, value):
        """Shortcut for the setter."""
        if not np.isfinite(value).all():
            raise ValueError("{} must be finite!".format(self.name))
        if self._nn and not np.all(value >= 0.0):
            raise ValueError("{} must be non-negative!".format(self.name))
        value = ensure_quantity(value, self._unit)
        return setattr(obj, self._attr, value)
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Get the property's value"""
        return self.get(obj)
        
    def get(self, obj):
        """Shortcut get method."""
        return self.recompose(getattr(obj, self._attr), self.bases(obj))
        
class ComputedUnitsProperty(UnitsProperty):
    """A units property computed from source."""
    def __init__(self, fget, warn_for_unit_composition=False):
        super(ComputedUnitsProperty, self).__init__(fget.__name__, None, False, warn_for_unit_composition)
        self.fget = fget
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Getter"""
        return self.recompose(self.fget(obj), self.bases(obj))
        
    def __set__(self):
        """Setter"""
        raise AttributeError("Can't set a computed property.")
        
class NonDimensionalProperty(UnitsProperty):
    """NonDimensionalProperty"""
    def __init__(self, name, unit, nonnegative=False, warn_for_unit_composition=False):
        super(NonDimensionalProperty, self).__init__(name, unit, nonnegative, warn_for_unit_composition)
        
    def nd_ensure_quantity(self, obj, quantity):
        """Return the non-dimensionalized unit."""
        return ensure_quantity(quantity, unscaled_unit(self._unit, self.bases(obj)))
        
    def bases(self, obj):
        """Get the non-dimensional bases."""
        if getattr(obj,'_is_nondimensional',False):
            return getattr(obj,'_nondimensional_bases',None)
        else:
            return super(NonDimensionalProperty, self).bases(obj)
    
    def __set__(self, obj, value):
        """Set this property's value"""
        if getattr(obj,'_is_nondimensional',False):
            value = self.nd_ensure_quantity(obj, value)
        super(NonDimensionalProperty, self).__set__(obj, value)

class InitialValueProperty(NonDimensionalProperty):
    """Initial Value Property"""
    
    def __init__(self, name, unit, nonnegative=False, warn_for_unit_composition=False):
        super(InitialValueProperty, self).__init__(name, unit, nonnegative, warn_for_unit_composition)
        self._init = '_{}_init_{}'.format(self.__class__.__name__, name.replace(" ", "_"))
        
    def get(self, obj):
        """docstring for get"""
        if getattr(obj, '_is_initial', False):
            return self.initial(obj)
        else:
            return super(InitialValueProperty, self).get(obj)
        
    def freeze(self, obj):
        """Freeze the value's initial state."""
        value = self.get(obj).copy()
        setattr(obj, self._init, value)
        
    def frozen(self, obj):
        """Frozen data"""
        return hasattr(obj, self._init)
    
    def initial(self, obj):
        """Get the initial value of a property."""
        if not hasattr(obj, self._init):
            raise FrozenError("{0}.{1} is not yet frozen.".format(obj,self.name))
        return self.recompose(getattr(obj, self._init), self.bases(obj))
        
class HasUnitsProperties(object):
    """docstring for HasUnitsProperties"""
    
    def _get_attr_by_name(self, name):
        """Get an attribute by its full name."""
        for element in dir(type(self)):
            attr = getattr(type(self), element)
            if isinstance(attr, UnitsProperty):
                if attr.name == name:
                    return attr
        raise AttributeError("{} has no property named {}".format(self, name))
        
    def get_unit(self, attr=None, name=None):
        """Get a property unit by attribute name or full name."""
        if attr is None:
            attr = self._get_attr_by_name(name)
        else:
            attr = getattr(type(self), attr)
        return attr.recomposed_unit(self)
        
        
class HasNonDimensonals(HasUnitsProperties):
    """A bass class for things which have non-dimensional variables."""
    
    _bases = None
    _nondimensional_bases = None
    _is_nondimensional = False
        
    def _list_attributes(self, klass):
        """Generate attributes matching a certain class."""
        for element in dir(type(self)):
            attr = getattr(type(self), element)
            if isinstance(attr, klass):
                yield element
        
    def _list_nd_variables(self):
        """List all of the state variables in this object's dir."""
        return self._list_attributes(NonDimensionalProperty)
        
    def _nd_properties(self):
        """Generator for state properties."""
        for element in self._list_nd_variables():
            yield getattr(type(self), element)
            
            
    @property
    def is_nondimensional(self):
        """A boolean determining whether the state is non-dimensional or not."""
        return self._is_nondimensional
        
    @property
    def nondimensional_bases(self):
        """Get the non-dimensional bases."""
        return self._nondimensional_bases
        
    @nondimensional_bases.setter
    def nondimensional_bases(self, value):
        """Set the non-dimensional bases."""
        if value is None and self._nondimensional_bases is None:
            return
        try:
            self._nondimensional_bases = set(value)
        except TypeError as e:
            raise TypeError("Non-dimensional bases should be a set of units.")
        
    def nondimensionalize(self):
        """Place the object in a non-dimensional state."""
        if not isinstance(self._nondimensional_bases, set) and len(self._nondimensional_bases) > 0:
            raise ValueError("{} has no non-dimensional bases.".format(self))
        self._is_nondimensional = True
        
    def dimensionalize(self):
        """Place the object in a dimensional state."""
        self._is_nondimensional = False
        
    @contextlib.contextmanager
    def in_nondimensional(self):
        """A context manager to put this object in the non-dimensional state."""
        self.nondimensionalize()
        yield self
        self.dimensionalize()
        
class HasInitialValues(HasNonDimensonals):
    """Base class for something which has non-dimensional properties."""
    
    _is_initial = False
    
    def _list_iv_variables(self):
        """List all of the state variables in this object's dir."""
        return self._list_attributes(InitialValueProperty)
        
    def _iv_properties(self):
        """Generator for state properties."""
        for element in self._list_iv_variables():
            yield getattr(type(self), element)
    
    @property
    def is_initial(self):
        """A boolean determining whether the state is non-dimensional or not."""
        return self._is_initial
        
    def initals(self):
        """Place the object in the initial state."""
        self._is_initial = True
        
    def actuals(self):
        """Place the object in the actual state."""
        self._is_initial = False
        
    def freeze(self):
        """Freeze this object."""
        for iv_property in self._iv_properties():
            iv_property.freeze(self)
            
    @property
    def frozen(self):
        """docstring for frozen"""
        return all([  iv_property.frozen(self) for iv_property in self._iv_properties() ])
        
    @contextlib.contextmanager
    def in_initial(self):
        """A context manager to put this object in the initial state."""
        self.initals()
        yield self
        self.actuals()