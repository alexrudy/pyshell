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
UNIT_MAX_DEPTH = 3
NON_DIMENSIONAL_FLAG = '_is_nondimensional'
INITIAL_VALUE_FLAG = '_is_initial'

def recompose(quantity, bases, scaled=False, warn_compositons=False, max_depth=UNIT_MAX_DEPTH):
    """Recompose a quantity in terms of the given bases.
    
    :param unit: The unit to recompose.
    :param bases: The set of units allowed in the final result.
    :param bool scaled: Whether to allow units with a scale or not.
    :param bool warn_compositons: Whether to warn when there were multiple compositions found.
    """
    result_unit = recompose_unit(quantity.unit, bases, scaled, warn_compositons, max_depth)
    result = quantity.to(result_unit)
    return result

def recompose_unit(unit, bases, scaled=False, warn_compositons=False, max_depth=UNIT_MAX_DEPTH):
    """Recompose a unit in terms of the provided bases.
    
    :param unit: The unit to recompose.
    :param bases: The set of units allowed in the final result.
    :param bool scaled: Whether to allow units with a scale or not.
    :param bool warn_compositons: Whether to warn when there were multiple compositions found.
    
    """
    composed = unit.compose(units=bases, max_depth=UNIT_MAX_DEPTH)
    if len(composed) != 1 and warn_compositons:
        warnings.warn("Multiple compositions are possible for {!r}: {!r}".format(unit,composed))
    result = composed[0]
    if result.scale == 1.0:
        return result
    elif scaled:
        return result
    else:
        unscaled = result / u.Unit(result.scale)
        return unscaled

class FrozenError(Exception):
    """An error occuring when trying to set frozen attributes."""
    pass

class UnitsProperty(object):
    """A descriptor which enforces units."""
    def __init__(self, name, unit, latex=None, nonnegative=False, readonly=False, scale=False, warn_for_unit_composition=False):
        super(UnitsProperty, self).__init__()
        self.name = name
        self.latex = name if latex is None else latex
        self._unit = unit
        self._attr = '_{}_{}'.format(self.__class__.__name__, name.replace(" ", "_"))
        self._nn = nonnegative
        self._readonly = readonly
        self._scale = scale
        self._warncompositon = warn_for_unit_composition
        
    def bases(self, obj):
        """Return the bases."""
        return getattr(obj, '_bases', None)
        
    def recompose(self, quantity, bases):
        """Recompose a unit into a new base set."""
        return recompose(quantity, bases, scaled=self._scale, warn_compositons=self._warncompositon)
        
    def unit(self, obj):
        """Get the recomposed unit."""
        return recompose_unit(self._unit, self.bases(obj), scaled=self._scale, warn_compositons=self._warncompositon)
        
    def __set__(self, obj, value):
        """Set this property's value"""
        if self._readonly:
            raise AttributeError("{} cannot set read-only attribute {}".format(obj, self.name))
        return self.set(obj, value)
        
    def set(self, obj, value):
        """Shortcut for the setter."""
        quantity = u.Quantity(value, unit=self.unit(obj))
        if not np.isfinite(quantity.value).all():
            raise ValueError("{} must be finite!".format(self.name))
        if self._nn and not np.all(quantity.value >= 0.0):
            raise ValueError("{} must be non-negative!".format(self.name))
        return setattr(obj, self._attr, quantity)
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Get the property's value"""
        return self.get(obj)
        
    def get(self, obj):
        """Shortcut get method."""
        value = getattr(obj, self._attr)
        recomposed = self.recompose(value, self.bases(obj))
        if value.unit != recomposed.unit:
            setattr(obj, self._attr, value)
            return recomposed
        return value
        
class ComputedUnitsProperty(UnitsProperty):
    """A units property computed from source."""
    def __init__(self, fget, readonly=True, warn_for_unit_composition=False):
        super(ComputedUnitsProperty, self).__init__(fget.__name__, None, readonly=True, scale=False,
            warn_for_unit_composition=warn_for_unit_composition)
        self.fget = fget
        
    @descriptor__get__
    def __get__(self, obj, objtype):
        """Getter which calls the property function."""
        return self.recompose(self.fget(obj), self.bases(obj))
        
        
class NonDimensionalProperty(UnitsProperty):
    """NonDimensionalProperty"""
    def __init__(self, name, unit, nonnegative=False, scale=False, warn_for_unit_composition=False):
        super(NonDimensionalProperty, self).__init__(name, unit, nonnegative=nonnegative, readonly=False, scale=scale,
            warn_for_unit_composition=warn_for_unit_composition)
    
    def bases(self, obj):
        """Get the non-dimensional bases."""
        if getattr(obj, NON_DIMENSIONAL_FLAG, False):
            return getattr(obj, '_nondimensional_bases', None)
        else:
            return super(NonDimensionalProperty, self).bases(obj)
        

class InitialValueProperty(NonDimensionalProperty):
    """Initial Value Property"""
    
    def __init__(self, name, unit, nonnegative=False, scale=False, warn_for_unit_composition=False):
        super(InitialValueProperty, self).__init__(name, unit, nonnegative=nonnegative, scale=scale,
            warn_for_unit_composition=warn_for_unit_composition)
        self._init = '_{}_init_{}'.format(self.__class__.__name__, name.replace(" ", "_"))
        
    def get(self, obj):
        """docstring for get"""
        if getattr(obj, INITIAL_VALUE_FLAG, False):
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
        return getattr(self, NON_DIMENSIONAL_FLAG)
        
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
        setattr(self, NON_DIMENSIONAL_FLAG, True)
        
    def dimensionalize(self):
        """Place the object in a dimensional state."""
        setattr(self, NON_DIMENSIONAL_FLAG, False)
        
    @contextlib.contextmanager
    def in_nondimensional(self):
        """A context manager to put this object in the non-dimensional state."""
        self.nondimensionalize()
        yield self
        self.dimensionalize()
        
setattr(HasNonDimensonals, NON_DIMENSIONAL_FLAG, False)
        
class HasInitialValues(HasNonDimensonals):
    """Base class for something which has non-dimensional properties."""
    
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
        return getattr(self, INITIAL_VALUE_FLAG)
        
    def initals(self):
        """Place the object in the initial state."""
        setattr(self, INITIAL_VALUE_FLAG, True)
        
    def actuals(self):
        """Place the object in the actual state."""
        setattr(self, INITIAL_VALUE_FLAG, False)
        
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
        
setattr(HasInitialValues, INITIAL_VALUE_FLAG, False)