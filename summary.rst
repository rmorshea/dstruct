``dstruct`` is designed to map larger data structures onto a smaller ones, which is simple in principle,
but can be complicated in practice - sifting through robust datasets is difficult when the structure
is highly nested, or relevant information is fractured. However, the module's intuitive api makes pruning
useless data, and parsing its relevant subsets easy.

- enables complex data parsing
- streamlines data trimming heuristics
- intuitive api for nested data structures

The implementation relies on the descriptor_ pattern.

.. _descriptor: https://docs.python.org/howto/descriptor.html

See GitHub_ for more info

.. _GitHub: https://github.com/rmorshea/dstruct