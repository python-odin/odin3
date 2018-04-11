######
Odin 3
######

Odin is a declarative framework for defining data-structures, their relationships, validation, 
mapping/transforming and serialisation. The core structure is a *Resource* (class). Serialisation
is provided for many common data formats (eg JSON, CSV, YAML).

Odin 3 is a complete refresh of the original Odin built with Python 3 (>=3.5) in mind.

Highlights
==========

* Class based declarative style (using Metaclasses)
* Field types for building composite Resources
* Field and Resource level validation
* Easy extension to support custom field types
* Python 3.5+ 
* Support for most native and standard library Python types (``str``, ``int``, ``float``, 
  ``bool``, ``date``, ``time``, ``datetime``, ``UUID``, ``Enum``)
* Support for formatted string types (eg *email*, *URL*)
* Integration with `Sphinx <http://sphinx-doc.org/>`_ for documenting structures
* Minimal dependencies (core library requires none!)
* Support for third party libraries (*Arrow*, *Pint*)

Use cases
=========

* Design, document and validate complex (and simple) data structures
* Convert structures between formats JSON -> Yaml
* Validate API inputs
* Define messaging formats for communicating via Message Queues (eg Rabbit MQ, SQS)
* Map API request to ORM objects

Quick links
===========

* `Project home <https://github.com/python-odin/odin3>`_
* `Issue tracker <https://github.com/python-odin/odin3/issues>`_

Requires
========

No other dependencies!

Optional
--------

* msgpack-python - For the msgpack codec
* pyyaml - For the YAML codec

Installation
============

From GitHub, download the latest release::

    python setup.py install
    
From PyPi::

    pip3 install odin


Example
=======

A simple book library, define a data-structure:: 

    import enum
    import odin
    
    class Genre(enum.Enum):
        ScienceFiction = "sci-fi"
        SpaceOpera = "space-opera"
        Fantasy = "fantasy"
    
    class Author(odin.Resource):
        name = odin.String
        
    class Publisher(odin.Resource):
        name = odin.String
        
    class Book(odin.Resource):
        title = odin.String
        authors = odin.ArrayOf(Author)
        genre = odin.Enum(Genre)
        num_pages = odin.Integer
        
Export to JSON::

    >>> from odin.codecs import json_codec
    >>> book = Book(
            title="Consider Phlebas",
            genre=Genre.SpaceOpera,
            publisher=Publisher(name="Macmillan")
            num_pages=471
        )
    >>> # Append an author
    >>> book.authors.append(Author(name="Iain M. Banks"))
    >>> # Export
    >>> json_codec.dumps(book, indent=4)
    {
        "$": "Book",
        "authors": [
            {
                "$": "Author",
                "name": "Iain M. Banks"
            }
        ],
        "genre": "space-opera",
        "num_pages": 471,
        "publisher": {
            "$": "Publisher",
            "name": "Macmillan"
        },
        "title": "Consider Phlebas"
    }
