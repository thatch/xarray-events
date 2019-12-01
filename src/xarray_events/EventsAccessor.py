"""Definition of the EventsAccessor class.

Define the EventsAccessor class with enough methods to act as a wrapper around
xarray extending its functionality to better support events data.

"""
from __future__ import annotations
from typing import Union
from pathlib import Path
from collections.abc import Collection, Callable

import xarray as xr
import pandas as pd

@xr.register_dataset_accessor('events')
class EventsAccessor:
    def _from_DataFrame(self, df: pd.DataFrame) -> None:
        """Helper method for load(source).

        If source is a DataFrame, assign it directly as an attribute of _ds.

        """
        self._ds = self._ds.assign_attrs(_events = df)

    def _from_csv() -> None:
        """Helper method for _from_Path(p).

        ! under construction !

        """
        pass

    def _from_Path(self, p: Path) -> None:
        """Helper method for load(source).

        If source is a Path, call the right handler depending on the extension.

        """
        if source.suffix == '.csv':
            self._from_csv()
        pass

    def _filter_events(self, constraints: dict) -> None:
        """Helper method for sel.

        Given a specified dict of constraints, filter the events DataFrame.

        The values for each constraint may be of different types, and the
        behavior varies accordingly. Here's how it works:

        - If the value is a Collection (like a list), filter the events by them.

        - If the value is a Callable (like a lambda function), filter the events
        by applying this function on the Series in each column of the DataFrame.

        - If the value is a single value, filter by it directly.

        """
        for k,v in constraints.items():

            # case where the specified value is a Collection
            if isinstance(v, Collection):
                self._ds.attrs['_events'] = self._ds._events[
                    self._ds._events[k].isin(v)
                ]

            # case where the specified value is a Callable
            if isinstance(v, Callable):
                self._ds.attrs['_events'] = self._ds._events[
                    self._ds._events[k].isin(self._ds._events[k].where(v))
                ]

            # case where the specified value is a single value
            else:
                self._ds.attrs['_events'] = self._ds._events[
                    self._ds._events[k] == v
                ]

    def __init__(self, ds) -> None:
        """xarray accessor with extended events-handling functionality.

        An xarray accessor that extends its functionality to handle events in a
        high-level way. This API makes it easy to load events into an existing
        Dataset from a variety of sources and perform selections on the events
        satisfying a set of specified constraints.

        Attributes:
            _ds (xr.Dataset): The Dataset to be accessed whose class-level
                functionality is to be extended.

        Arguments:
            ds (xr.Dataset): Same as _ds.

        """
        self._ds = ds

    def load(self, source: Union[pd.DataFrame, Path, str]) -> xr.Dataset:
        """Set the events DataFrame as an attribute of _ds.

        Depending on the source where the events are to be found, fetch and load
        them accordingly.

        Usage:
            First method that should be called on a Dataset upon using this API.

        Arguments:
            source (DataFrame/PosixPath/str): A DataFrame or Path specifying
                where the events are to be loaded from.

        Returns:
            self, which contains the modified _ds now including events.

        Raises:
            TypeError: if source is neither a DataFrame nor a Path.

        """
        # a DataFrame is the ultimate way of representing the events
        if isinstance(source, pd.DataFrame):
            self._from_DataFrame(source)

        # if a Path is given:
        #   1. fetch the data depending on the file extension
        #   2. convert it into a DataFrame
        elif isinstance(source, Path):
            self._from_Path(source)

        # if a string is given, and assuming it corresponds with a path:
        #   1. convert it into a Path
        #   2. handle it accordingly
        elif isinstance(source, str):
            self._from_Path(Path(source))

        else:
            raise TypeError(
                f'Unexpected type {type(source).__name__!r}. Expected Dataframe'
                ', str or Path instead.'
            )

        return self._ds

    def sel(self, indexers: Mapping[Hashable, Any] = None, method: str = None,
            tolerance: numbers.Number = None, drop: bool = False,
            **indexers_kwargs: Any) -> xr.Dataset:
        """Perform a selection on _ds given a specified set of constraints.

        This is a wrapper around xr.Dataset.sel that extends its functionality
        to support events handling.

        The arguments that match events DataFrame attributes are used to filter
        the events. Everything else is passed directly to xr.Dataset.sel.

        Usage:
            Call by specifying constraints for both the Dataset dimensions and
            the events DataFrame attributes in a single dictionary.

        Tip: If intended to be chained, call after having called load to ensure
        that the events are properly loaded.

        The arguments, return values and raised exceptions are the same as for
        xr.Dataset.sel, in order to stay true to the wrapper nature of this
        method. See the official xarray documentation for details.

        """
        # constraints may refer to either Dataset dimensions or events attrs
        constraints = {**indexers, **indexers_kwargs}

        d = set(self._ds.dims) # Dataset dimensions

        # events attributes, which may not exist
        e = set(self._ds.attrs['_events'].columns if self._ds.attrs else {})

        # call xr.Dataset.sel with the method args as well as all constraints
        # that match Dataset dimensions
        self._ds = self._ds.sel(
            {k:constraints[k] for k in set(constraints) & d},
            method, tolerance, drop
        )

        # filter the events DataFrame by the appropriate constraints
        self._filter_events({k:constraints[k] for k in set(constraints) & e})

        # TODO: Here's a good place to drop "out-of-view" events.

        return self._ds