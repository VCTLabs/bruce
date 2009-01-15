.. style: :transition.name: none

page one

----

.. style:: :list.expose: expose

- this is a bullet list
- with expose (not fade) turned on
- .. image:: sample-image.png
- last item

----

.. style:: :list.expose: fade

1. numbered list with fade expose on
2. .. image:: sample-image.png
3. ========= =========
   Heading 1 Heading 2
   ========= =========
   Cell 1    Cell 2
   Cell 3    Cell 4
   ========= =========
4. .. interpreter::
      :width: 700
      :height: 100
5. last item

----

this is a definition list
  definition

next item
  .. image:: sample-image.png

last item
  blah

----

.. style:: :list.expose: show

- list expose
- turned off
- all items visible
- last item

