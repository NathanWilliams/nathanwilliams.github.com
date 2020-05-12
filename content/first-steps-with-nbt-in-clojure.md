Title: First steps with NBT in Clojure
Author: Nathan Williams
Date: 2013-02-25 12:54
tags: Clojure, Minecraft, NBT, Gloss
category: programming

In the [last post][prevpost] we covered the basics of the NBT structure.
Now it is time to start reading a basic NBT test file.
I am going to start with "test.nbt" provided by Markus Persson (aka Notch), and in this entry we are  going to do the bare minimum to read the file.

This post assumes a working Clojure environment, including Leiningen.

[prevpost]: http://nathanwilliams.github.com/2013/02/23/exploring-minecraft-with-clojure/ "Exploring Minecraft with Clojure"


Reading Binary data in Clojure
------------------------------

To start off, we need to decide how to read the binary files in Clojure.
We could drop down to Java and use java.nio, but that seems so primitive...
<!-- PELICAN_END_SUMMARY -->

Enter Gloss
-----------

A better option is the [Gloss][gloss] DSL / library, which provides a nice, high level way of processing binary data in Clojure.
[gloss]: https://github.com/ztellman/gloss "Gloss DSL"


With Gloss you specify what makes up a "frame" and compile it into a codec which you can use to decode or encode structured binary data.
A frame consists of other codecs, and eventually all codecs come down to primitive values such as bytes, numbers and strings.

Gloss also provides a set of codecs that handle variable length data, such as repeated.
Instead of covering what is available in Gloss, you should have a quick look at its [Introduction page][gloss-intro].

[gloss-intro]: https://github.com/ztellman/gloss/wiki/Introduction "An introduction to Gloss"

Preparation
-----------

Before we go any further, make a clone of the repo for this post here: [nbt-basic]
This provides the end result to this post, but also provides the test file and some code to load it for easy experimentation in the repl.

Once you clone the repository, change into the project directory, and run:

    :::bash 
    lein deps
    lein repl

From here you will want to change into the 'nbt-basic.devel' namespace, and load the 'refresh' function from the tools lib, and finally call refresh

    :::clojure REPL setup for experimenting
    (ns nbt-basic.devel)
    (use '[clojure.tools.namespace.repl :only (refresh)])
    (refresh)

This will make sure everything is loaded, and that you can easily access the already loaded data file.
If you make any changes to the files, simply call refresh again, which will clear out the repl environment and reload any changes.



The Goal
--------

The plan for this post is to handle the simple test.nbt file, which decoded looks something like this:

    TAG_Compound('hello world'): 1 entry
    {
        TAG_String('name'): 'Bananrama'
    }

The byte data looks like this:

    0a 00 0b 68 65 6c 6c 6f 20 77 6f 72 6c 64 08 00
    04 6e 61 6d 65 00 09 42 61 6e 61 6e 72 61 6d 61
    00

Referencing back to the NBT specification on the [MinecraftCoalition wiki page][nbt], we can start to decode the data.
Looking at the specification, we have the following:

 - All files start with a TAG_Compound
 - A TAG_Compound starts with an ID of 10 (0x0a) and is terminated by a TAG_End which has an ID of 0 (0x00)

[nbt]: http://mc.kev009.com/NBT "The NBT spec on the MinecraftCoalition wiki"
[nbt-basic]: https://github.com/NathanWilliams/nbt-basic

So lets start with the simplest thing that would work:

    :::clojure Overly simple codec
    (defcodec tag-compound-ugly
      (ordered-map  :tag-type tag-type
                    :tag-name sized-string
                    :child    tag-type
                    :payload  tag-string
                    :end      :byte))

This codec is almost useless as it is hardcoded for this file structure only, but it serves a purpose of explaining a few Gloss concepts.

At the repl, type:

    :::clojure Using the codec
    (decode tag-compound-ugly data)

You should get the following out:

    :::clojure
    {:end 0, :payload {:payload "Bananrama", :tag-name "name", :tag-type :TAG_String}, :child :TAG_String, :tag-name "hello world", :tag-type :TAG_Compound}

If you look back at the decoded version of this file shown earlier, you should see that our codec has worked!


But how did it work?
Lets break it down into its component pieces.

__defcodec__: This simply compiles the frame and binds it to a var, and is equivalent to:

    :::clojure
    (def name (compile-frame body))

__compile-frame__: This takes either a single codec, a vector of codecs, a map or an *ordered-map*

- A single codec can be anything from a primative (numbers, strings) to something like a *repeated* construct.
- A vector is ordered, and the codec will produce a vector on decode, and consume one on encode.
- A map is a normal Clojure map and is not ordered.
  The order is consistent however, which is useful for working with other Gloss code, but cannot be used with an already defined binary format order.
- An ordered-map is a Gloss construct that allows you to use a Clojure map on encode & decode, whilst maintaining the defined order.

__frames__: Along with codecs, a frame can take constant values, which are not taken from the binary data on decoding, and are not added on encoding.
Instead, these are useful for providing map keys, or other constants such as an internal name, to help identification in the rest of your code.


If you look at our *tag-compound-ugly*, you will see a list of keys, paired with codecs.
All of the codecs (except for the final ":byte") are defined in the project repository that you cloned previously, in "src/nbt_basic/nbt.clj".


So now we can look at how each of these codecs are defined, so we can put the whole picture together.

__tag-type__

    :::clojure tag-type codec
    (defcodec tag-type (enum :byte {:TAG_String     8
                                    :TAG_Compound   10}))

The tag-type codec uses Gloss' *enum* codec, which takes a primative codec, and converts between the raw value and what you provide.
This allows you to turn magic values from a binary format into something readable.
This implementation of tag-type is incomplete, only covering the two data types in the test.nbt file.

__sized-string__

    :::clojure sized-string codec
    (defcodec sized-string (finite-frame :uint16-be
                                         (string :utf-8)))

The sized-string codec wraps a string codec in a *finite-frame*.
The finite-frame takes a codec which returns a count of bytes, and then gives that number of bytes to its child codec, in this case a utf-8 string.
This matches the NBT specification which marks a string (both the name of an object, and the contents of a TAG_String) with an unsigned short (16 bits / 2 bytes) in big-endian format (hence the -be postfix).

And finally we have *tag-string*.

    :::clojure tag-string codec
    (defcodec tag-string
      (ordered-map :tag-type    :TAG_String
                   :tag-name    sized-string
                   :payload     sized-string))

With the exception of TAG_List items (which we will cover another time), NBT tags are named.
So a TAG_String consists of two *sized-string* codecs, one for the tag's name, and the other its contents. 


Conclusion
----------

We have covered a lot of stuff, but it doesn't feel we have gotten very far!
That is going to change quickly, now that you have a better understanding of how Gloss works, next time we will cover a complete reader that will be able to read any NBT structure.

Feedback
--------

As before, if you see something wrong, fork this blog post on GitHub, fix it and send me a pull request.
If you have questions or suggestions, please raise a ticket against it and I'll get back to you.
