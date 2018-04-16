############################
Migrating from Odin to Odin3
############################

While the much of the interaction with Odin3 remains the same there have been
some changes that could catch developers.

ABCs and Typing
===============

Odin 3 makes extensive use of the :mod:`typing` and the :mod:`abc` modules.
This has necessitated some changes to the location of base classes used as
interfaces to prevent circular dependencies (there are work around solutions
documented by :mod:`mypy`, however, the best solution is still one that
prevents the need for using a work around).

To this end all ABC classes are now defined in :mod:`odin.bases`.

Validation Error Messages
=========================

These have all been migrated to use :func:`str.format`.

Utils
=====

The :mod:`odin.utils` module has been re-organised into more logical blocks.
This module was becoming a dumping ground for utility functions, by splitting
into separate modules the available functions becomes easier to find and
documentation and testing can be more focused.
