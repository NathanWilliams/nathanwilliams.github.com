Title: Exploring Minecraft with Clojure
Author: Nathan Williams
Date: 2013-02-23 06:14
tags: Clojure, Minecraft, NBT
category: programming

After years of ignoring it, I have become hooked on Minecraft after a single try.
Looking from the outside, all you see is a low resolution, blocky world; but jump in and you find yourself in a vast, detailed expanse.

The low resolution fades before your eyes.
Like a good book, your imagination fills the gaps, you don't see a lego shaped hill, you see a mountain forged through eons of time.

Before you know what has happened, you have made a mark on that world.
You own it, you mold it, you get a feel for the lay of the land, you push boundries and find them surprisingly maleable.
The pieces might be simple, but the outcome is rich and intricate.

I find something deeply similar with Clojure.
From the outside you see a strange syntax, terse and compact, you wonder how anything can be done in it.
Where is the required boilerplate you need to paste in, where is the dense documentation to wade through?

But you jump in anyway.
You struggle at first, your previous experience didn't prepared you for this, but you see something special, so you persist.
Before you know it, you have made something interesting, and the result is elegant and compact.

The strange syntax fades, and you don't miss the verbosity you once thought was necessary to achieve impressive feats.

Exploration
-----------

So how does this journey begin you ask?
Like any good Clojure task, we are going to start from low level building blocks and compose our way to something bigger.
The starting point of this expedition is in reading the [Named Binary Tag][nbt] data structure that is used extensively in Minecraft data files and network communications.
<!-- PELICAN_END_SUMMARY -->

The NBT format
--------------
NBT is a simple binary format that stores data tagged by type, and unless part of list, they are also named.
Here is a simple example of a (decoded) NBT structure:

    TAG_Compound('hello world'): 1 entry
    {
        TAG_String('name'): 'Bananrama'
    }

On disk, this file looks like this:

    0000000 0a 00 0b 68 65 6c 6c 6f 20 77 6f 72 6c 64 08 00
    0000010 04 6e 61 6d 65 00 09 42 61 6e 61 6e 72 61 6d 61
    0000020 00                                             
    0000021

The format allows more than just a flat group of objects, elements can be nested inside compound and list data structures to an arbitrary depth.

Here is a more complex example:


     TAG_Compound('Level'): 11 entries
     {
       TAG_Compound('nested compound test'): 2 entries
       {
         TAG_Compound('egg'): 2 entries
         {
           TAG_String('name'): 'Eggbert'
           TAG_Float('value'): 0.5
         }
         TAG_Compound('ham'): 2 entries
         {
           TAG_String('name'): 'Hampus'
           TAG_Float('value'): 0.75
         }
       }
       TAG_Int('intTest'): 2147483647
       TAG_Byte('byteTest'): 127
       TAG_String('stringTest'): 'HELLO WORLD THIS IS A TEST STRING \xc3\x85\xc3\x84\xc3\x96!'
       TAG_List('listTest (long)'): 5 entries
       {
         TAG_Long(None): 11
         TAG_Long(None): 12
         TAG_Long(None): 13
         TAG_Long(None): 14
         TAG_Long(None): 15
       }
       TAG_Double('doubleTest'): 0.49312871321823148
       TAG_Float('floatTest'): 0.49823147058486938
       TAG_Long('longTest'): 9223372036854775807L
       TAG_List('listTest (compound)'): 2 entries
       {
         TAG_Compound(None): 2 entries
         {
           TAG_Long('created-on'): 1264099775885L
           TAG_String('name'): 'Compound tag #0'
         }
         TAG_Compound(None): 2 entries
         {
           TAG_Long('created-on'): 1264099775885L
           TAG_String('name'): 'Compound tag #1'
         }
       }
       TAG_Byte_Array('byteArrayTest (the first 1000 values of (n*n*255+n*7)%100, starting with n=0 (0, 62, 34, 16, 8, ...))'): [1000 bytes]
       TAG_Short('shortTest'): 32767
     }

I'm not going to cover the entire NBT specification, as it is already well covered on the [MinecraftCoalition wiki page][nbt].

There are however a few gotchas that might trip you up along the way.

- TAG_Byte_Array & TAG_Int_Array don't hold tagged data, only raw bytes / integers.
- Every tag starts with a single byte for type id.
- Tags contain a string name, which is the same structure as a TAG_String, just without the string tag id.
- TAG_List breaks the above two rules (tag id and name) for its immediate child nodes. 
  A TAG_List contains the tag id for its child objects, so all direct decendant nodes are of the same type, and a signed integer indicating the number of elements in the list.


Conclusion 
----------

I know we haven't covered any Clojure yet, but I wanted to get the basics out of the way first, so we can jump into code without having to go back and forth constantly.
The next entry we will look at reading a simple NBT file, covering the bare minimum, and then building from there.


Feedback
--------

You may have noticed the lack of comments on this blog.

This is a concious decision, but it doesn't mean I don't want feedback.
If you see something wrong from typos and grammer to bad coding practices, I want to know!

This blog is hosted on [GitHub][gh] so feel free to fork it, make corrections and issue a pull request.
You can also raise a ticket to suggest improvements, or ask for clarification on anything I haven't explained clearly.


[nbt]: http://mc.kev009.com/NBT "The NBT spec on the MinecraftCoalition wiki"
[gh]: https://github.com/NathanWilliams/nathanwilliams.github.com/tree/source "Blog source tree"
