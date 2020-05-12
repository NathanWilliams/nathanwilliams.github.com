Title: Seesaw, GUI programming the Clojure way
Author: Nathan Williams
Date: 2013-05-15 17:06
tags: Clojure, Minecraft, Region, Seesaw, Swing, Gui
category: programming


In this post we are going to look at how to make a GUI in Clojure without the ugliness that is Swing.
Seesaw is a Clojure library that wraps Swing making it easier to work with and with much less code.

Keeping with the Minecraft theme, we will be expanding on the previous posts and visualising a Minecraft Anvil / Region file.

If you are new to this series, jump back and have a look at the previous post to catch up: [Minecraft Region Files][regionfiles]

[regionfiles]: http://nathanwilliams.github.io/2013/04/16/minecraft-region-files/
<!-- PELICAN_END_SUMMARY -->

Preparation
===========

As always, the code to go along with this post can be found on GitHub, so clone the [anvil-view] repo and launch a repl:
[anvil-view]: https://github.com/NathanWilliams/anvil-view

    :::bash
    lein deps
    lein repl

The GUI
=======

With the REPL up, type the following to bring up the finished product:

    :::clojure
    (show-gui)

You should get the following window:

![Anvil View]({static}/images/anvilview.png)

So by now you may have realised that GUI layout is not my strong point!
The interface is ugly, but functional.

At the top you have three menus, the first lists the Minecraft worlds you have on your computer (looking in the standard Minecraft directory), the second is the dimension and the last is the Anvil file.

Below the screen is divided into four quadrants.
The top left is a representation of the header file, with white blocks being empty, and green being used.

As you move the mouse over this view, the quadrant at the top right displays information for that record, and the quadrant at the bottom left highlights the data referenced by that header block.

The bottom left is the layout of chunk data in the file, with the first two sectors taken by the header (each sector being 4096 bytes, and the header being 2 sectors).

The bottom right was meant to be a display of NBT data, and it was almost working in a tree, but is currently disabled so this post could at least be made!

The Code
========

The code has been divided into a Model-View-Controller pattern, with an attempt at keeping different concepts isolated.

As this post is focusing on GUI programming, it will be limited to covering the view.clj and controller.clj files.
Hopefully the rest should be reasonably easy to follow based on previous posts.

To start out, lets talk about Seesaw and Swing.

Seesaw & Swing
==============

If you have ever created a GUI in Java before, you will have come across Swing.
Swing is the main Java API for creating GUIs, and it is a bit of a beast to learn and work with.

Seesaw is a Clojure library that wraps Swing and tries to make life more plesent, to make things clearer, and to do some of the heavy lifting for you.

Seesaw can be found here: [Seesaw]
[Seesaw]: https://github.com/daveray/seesaw

Frames & Panels
===============

To create a GUI in Swing, you need a *frame* (a window) and you divide it up by using *panels*.

Panels come in many forms and help control your layout when the size of your window changes, helping your widgets and layout stretch proportionally to each other.

Open up view.clj, and look for "main-window":

    :::clojure main-window
    (def main-window
      (sc/frame :title title
                :width (:width window-size)
                :height (:height window-size)
                :content window-content))

This is how we define the window you saw earlier.
"sc" is the name I gave seesaw.core when I required it.
sc/frame creates a JFrame with its options being passed in as pairs of keys and values.

Not all values are required, anything not specified reverts to default values.
The options above are self explanatory, but how do you know what options are available?

This is one of the shining points of seesaw, it has great development support in the REPL.

In the REPL you launched earlier, type the following:

    :::clojure
    (use 'seesaw.dev)
    (use 'seesaw.core)

    (show-options (frame))

You will get back something like the following:

    :::clojure

    seesaw.core.proxy$javax.swing.JFrame$Tag$a79ba523
                        Option  Notes/Examples
    --------------------------  --------------
                        :class  A keyword class, in the HTML/CSS sense.
                                See (Seesaw.core/select)
                      :content  The frame's main content widget
                         :icon
                           :id  A keyword id.
                                See (seesaw.core/select)
                      :menubar  The frame's menu bar. See (seesaw.core/menubar).
                 :minimum-size  [640 :by 480]
                                java.awt.Dimension
                     :on-close  :hide
                                :dispose
                                :exit
                                :nothing
                   :resizable?
                     :resource  A i18n prefix for a resource with keys
                                [:title :icon]
                         :size
                        :title  The frame's title as string or resource key
             :transfer-handler  See (seesaw.dnd/to-transfer-handler)
                 :undecorated?
                     :visible?


This handy tool can be used to on any of the Seesaw elements, and is really helpful for exploring what is possible.

If you have read through the options above, you may have noticed the *class* and *id* options.
We will cover this more later, but in brief, if you have ever worked with CSS selectors, you will find these options very useful.


Before we move on, we should quickly have a look at what the contents of our *main-window* are:

    :::clojure window-content
    (def window-content
      (sc/border-panel
         :north  world-selector
         :center (sc/vertical-panel
                    :items [header-panel sector-panel])))

This is the first panel we use, and it contains all other panels.
A border-panel is a "BorderLayout" in Java terms, and breaks up into five sections, the points of the compass and a centre.

In this case we are only using the north (for the world selection menus) and the centre (or 'center' for our American friends!) for the rest of the GUI.

If you follow the definition of each, you will find more panels dividing up those subsections in different ways.
It is almost like a set of Russian dolls, with panels inside of panels!

User Input
==========

An interface isn't much fun if you can't interact with it, so lets look at the two ways you can interact with this interface.

First we have the menus to select the anvil file to load, and then we have the mouse-over effect when you hover over the header to see the sector(s) it references.


Comboboxes
----------

The world / dimension / file selector is implemented as a set of combobox widgets.

    :::clojure world-selector
    (def world-selector
      "Used to select the world, dimension and anvil file to view"
      (sc/horizontal-panel
         :items [(sc/combobox :model worldlist               :id :worldlist)
                 (sc/combobox :model worlds/dimension-names  :id :dimension)
                 (sc/combobox :model files                   :id :files)]))

Here we simply create them directly in the panel that holds them, supplying a data model and an id to reference them by later.

The id is used just like an id in a HTML document and can be selected just like you would with a CSS selector.

The model is just some form of data structure to fill the combobox with.
When you select a world, or a dimension, the list of files to pick from will change, so we will need to be able to change the model when that happens.

When a change is detected, we can update the file list with the following:

    :::clojure update-files
    (defn update-files []
      (sc/config! (sc/select main-window [:#files])
                  :model (worlds/get-files (get-world) (get-dimension))))

This is where we make use of the id we created earlier, and we update the config of the element, switching out its current model with a new one.

*select* is Seesaw's way of getting an object without you having to hold a reference somewhere.
It takes the parent frame, and a CSS like selector.

*config!* takes the element returned from the select, and gives it a new model value returned by the "get-files" function.

Now that we have created the comboboxes, we need a way to know when they have changed and a way to get their value.

Listeners
---------

To be notified of when an event happens on a widget, you need to register a listener.
Seesaw makes this really simply with the *listen* function.

Open controller.clj and have a look at setup-listeners

    :::clojure setup-listeners
    (defn setup-listeners []
      (sc/listen (sc/select view/main-window [:#worldlist])
                 :selection world-changed)
      (sc/listen (sc/select view/main-window [:#dimension])
                 :selection dimension-changed)
      (sc/listen (sc/select view/main-window [:#files])
                 :selection file-changed)
      (sc/listen view/header-canvas
                 :mouse-moved header-mouse-moved))

Al you need to do is pass in an object (which we get using select in this case) and pairs of events and functions to handle that event.

As before, if you want to know what type of events are available for a given element, the Seesaw dev tools make it really simple:

    :::clojure 
    (use 'seesaw.dev)
    (show-events (combobox))

This gives the following list:

    :::clojure
    :action [java.awt.event.ActionListener]
      :action-performed
    :component [java.awt.event.ComponentListener]
      :component-hidden
      :component-moved
      :component-resized
      :component-shown
    :focus [java.awt.event.FocusListener]
      :focus-gained
      :focus-lost
    :item [java.awt.event.ItemListener]
      :item-state-changed
    :key [java.awt.event.KeyListener]
      :key-pressed
      :key-released
      :key-typed
    :mouse [java.awt.event.MouseListener]
      :mouse-clicked
      :mouse-entered
      :mouse-exited
      :mouse-pressed
      :mouse-released
    :mouse-motion [java.awt.event.MouseMotionListener]
      :mouse-dragged
      :mouse-moved
    :mouse-wheel [java.awt.event.MouseWheelListener]
      :mouse-wheel-moved
    :property-change [java.beans.PropertyChangeListener]
      :property-change
    :selection [java.awt.event.ActionListener]
      :action-performed

The beauty of this system is that you don't need to make a class that conforms to a certain listener interface just to provide a simple callback method.
All you need is a Clojure function, and Seesaw does the rest.

Although we don't make use of it here, *listen* returns a function that when called removes the listener created by the call.

Getting the value
-----------------

Now that you can trigger a callback on a change, all you need now is a way to get the value.

Here Seesaw provides a simple function that works across all of the various widgets, simply called *value*.

Here is how we get the selected file:

    :::clojure get-file
    (defn get-file []
      (sc/value (sc/select main-window [:#files])))

So clean and simple, Seesaw really does make it nicer to code a GUI!

Output
======

All that is left now, is to show the user something in response to their actions.
In this application we have two forms of output.
One is drawing to the two canvases, and the other is textual information in a table.

There were plans for a tree to display the NBT data, but that has been problematic and I didn't want to hold this post up for that one piece.

The Canvas
----------

Drawing in the canvas consists of drawing a list of primitives such as rectangles, circles, polygons etc.

Creating a canvas element in Seesaw is once again a very simple process:

    :::clojure header-canvas and sector-canvas
    (def header-canvas
      (sc/canvas :id         :headercanvas
                 :background :white))

    (def sector-canvas
      (sc/canvas :id         :sectorcanvas
                 :background :white))

This should look familiar, and is one of the real strengths in Seesaw where the various elements all share the same creation interface.

As id has been given to both canvases, but as we store them in a var, this isn't really needed.
All we are defining right now is the background colour.

There isn't much more to say about them, they are really this simple!
They do however offer many more options, so don't forget to call show-options in a repl to see what is available.

Now that we have a canvas, we can start drawing into them.

Before we can however, we need to define a paint function.
This could have been added at creation, but to keep the code a bit clearer, I decided to delay it to a later point in the code.

Changing a setting on an element is simple though, just like we did with the comboboxes, we just need to call config!:

    :::clojure init-view
    (defn init-view []
      ; Config the paint functions etc
      (sc/config! header-canvas :paint paint-header)
      (sc/config! sector-canvas :paint paint-body))

Starting with the header's paint function:

    :::clojure paint-header
    (defn paint-header [context graphics]
      (apply sg/draw graphics
        (apply concat (render-header))))

It might be a bit hard to understand this without knowing what render-header is returning, so lets try a simpler example quickly:

    :::clojure example
    (defn paint [c g]
       (draw g (rect 0 0 10 10)
               (style :foreground (scolor/color :black))))

This example would simply draw a 10x10 rectangle at 0,0 (top left of its parent) and would use draw it in black.

All *draw* takes is a sequence of primitives and the style to apply to them.
Now if you read paint-header, you should be able to guess that render-header returns a sequence of primitives and styles, we simply concat it all into a sinle sequence, and then use apply to pass the contents of that sequence to draw as arguments.

The rest of the drawing routine is simply a way to create that sequence of primitives (rectangles) and their style (green if used, white / empty if not):

    :::clojure render-header and render-record
    (defn render-record [row col rec]
      [(sg/rect (* 10 col) (* 10 row) 8 8)
       (if (chunk-model/empty-chunk? rec)
         empty-style
         used-style)])

    (defn render-header []
      (apply concat
        (map-indexed
         (fn [z-index rowdata] (map-indexed (partial render-record z-index) rowdata))
             (selected-header))))

I'm not going to go down every path here as it relies on the data models that aren't going to be examined today.
But put simply, render-header gets the value of each header record, and uses render-record to draw the appropriate rectangle.

render-record is the more interesting function.
It returns a vector of two elements, the rectangle whose position is determined by the row and column of the data, and the style is selected based on if the header is refering to data with any size (an empty-chunk is defined as one having zero size).


Painting the sectors is very similar, but with the addition of the highlighted sectors when you move the mouse over the header.

    :::clojure Rendering the sectors
    (def sectors-per-row 40)

    (defn render-sector [i s]
      (let [x (rem i sectors-per-row)
            y (quot i sectors-per-row)]
        [(sg/rect (* 10 x) (* 10 y) 8 8)
         (cond (contains? @highlight-sectors i) highlight-style
               s                                used-style
               :default                         empty-style)]))

    (defn render-sectors []
      (apply concat
        (map-indexed render-sector
           (file-model/ordered-sectors (selected-header)))))

    (defn paint-body [context graphics]
      (apply sg/draw graphics (render-sectors)))

If the sector being drawn is in the *highlight-sectors* atom, then it is given an orange style, if the sector is not empty (*s* is true) it is given a green style and otherwise it is given a white / empty style.

The positioning of the rectangles is a bit of a lazy hack, using a magic value *sectors-per-row* but it kept things simple for now.


Tables
------

The last bit of information we have to display are things like the timestamp of the latest update for the highlighted chunk.
For this a table is used, and once again, Seesaw makes life easy.

Creating the table is pretty much self explanatory by now:

    :::clojure header-info
    (def header-info
      (sc/table
       :model [:columns [{:key :var   :text "Variable"}
                         {:key :value :text "Value"}]

               :rows    [{:var "Offset"    :value "0"}
                         {:var "Size"      :value "0"}
                         {:var "Timestamp" :value "0"}
                         {:var "X"         :value "0"}
                         {:var "Z"         :value "0"}]]))

Just like the combobox, you supply a model of your data.
The model is a vector of the columns and the rows, with each being defined in Clojure maps.
The names you give the columns, you then use in the rows, so you can supply data in any order, and even leave it out for some rows as you need to.
In this case we could have left the :value out of the rows and we would have been given empty cells instead.
Updating the values in the table is also really simple, all you need is the update-at! function:

    :::clojure update-header-info
    (defn update-header-info [x z]
      (when-let [c (chunk-model/get-chunk (selected-header) x z)]
        (st/update-at! header-info 0 {:value (chunk-model/chunk-sector-location c)}
                                   1 {:value (chunk-model/chunk-sector-size c)}
                                   2 {:value (chunk-model/chunk-timestamp c)}
                                   3 {:value x}
                                   4 {:value z})))

You give the table to update, and then pairs of row index and the value to change.
We don't need to change the first column (:var) just the second, so we only supply an updated value for that column.


Conclusion
==========

That ended up being a much bigger post than I expected, and I feel I left so much of the code behind.
I guess I need to learn to do these things in smaller chunks so I can post more frequently and with smaller amounts of explainations to pack in!

As always, if you see a mistake in any of the above, from grammer and spelling to coding, clone the Git repo for the blog, make the change and send me a pull request.
If you have suggestions or questions, raise an issue and I will get back to you.


Next Time
=========

I'm thinking of taking a break from Clojure & Minecraft for a while.
It has been a lot of fun, and a great way to improve my Clojure skills, but I am itching to do something different.

Maybe some microcontrollers, or some Objective-C, I feel I have let both skills stagnate a bit, so it might be time to challenge myself again!


