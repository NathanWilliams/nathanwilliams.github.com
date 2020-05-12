Title: Reading Minecraft NBT data in Clojure with Gloss
Author: Nathan Williams
Date: 2013-02-27 08:13
tags: Clojure, Minecraft, NBT, Gloss
category: programming


So far we have covered what makes up an NBT file in [Exploring Minecraft With Clojure][nbt-post] and how to read binary data in Clojure using the Gloss DSL in [First Steps With NBT in Clojure][gloss-post]

[nbt-post]: http://nathanwilliams.github.com/2013/02/23/exploring-minecraft-with-clojure/ "An introduction to the NBT binary structure"
[gloss-post]: http://nathanwilliams.github.com/2013/02/25/first-steps-with-nbt-in-clojure/ "An introduction to reading binary data with Gloss"


Today we are going to make a parser that can read any NBT file.
There will be more code than last time, but only a small amount of it will really be new, the rest should be easy to understand based on what we have already covered.
<!-- PELICAN_END_SUMMARY -->

Preparation
-----------

You will want to clone the repository that accompanies this post from here [nbt-clj-reader]

[nbt-clj-reader]: https://github.com/NathanWilliams/nbt-clj-reader "An example of reading NBT files in Clojure"

As before, the project comes with a devel file to make setup easy, change into the project root and type:

    :::bash
    lein deps
    lein repl

At the Clojure REPL, type:

    :::clojure
    (ns nbt-clj-reader.devel)
    (use '[clojure.tools.namespace.repl :only (refresh)])
    (refresh)

This gives you a "data" var, where an NBT file has already been loaded into, and a "result" var, which has the decoded value of that file.


The new stuff
-------------

As mentioned earlier, a lot of the new code should be obvious from what was covered in the previous post.
For example *tag-type* has simply been expanded to cover all of the tags in NBT:

    :::clojure The complete tag-type codec
    (defcodec tag-type (enum :byte {:TAG_End        0
                                    :TAG_Byte       1
                                    :TAG_Short      2
                                    :TAG_Int        3
                                    :TAG_Long       4
                                    :TAG_Float      5
                                    :TAG_Double     6
                                    :TAG_Byte_Array 7
                                    :TAG_String     8
                                    :TAG_List       9
                                    :TAG_Compound   10
                                    :TAG_Int_Array  11}))

Named & Unnamed codecs
----------------------

The other new codecs such as *tag-byte*, *tag-float* etc are largely self explanatory, but with one big difference compared to last time, and that is that they no longer have their "name" codec defined:

    :::clojure tag-byte and tag-float codecs
    (defcodec tag-byte
      (ordered-map :tag-type    :TAG_Byte
                   :payload     :byte))
    (defcodec tag-float
      (ordered-map :tag-type    :TAG_Float
                   :payload     :float32-be))


The lack of name is due to the fact that a tag is nameless when used in a list.
For all other times, when a name is used, we handle it with a wrapper codec:

    :::clojure Adding a name to a codec
    (defn get-named-codec [t]
      (compile-frame
        (ordered-map  :tag-name    sized-string
                      :payload (get-codec t))
        identity ;pre-encoder
        (fn [x] (merge x (:payload x)))))

By doing this, we can have both named and unnamed codecs without having to redefine them twice.
This codec has some additional properties in adding a post-decoder callback (and a do-nothing pre-encoder callback).

The codec that comes out of this function starts with a sized-string (the tag's name), and then the codec for that tag (using "get-codec" which we will cover later in this post).
Doing it like this however give a result like this:

    :::clojure
    {:payload {:payload "Bananrama", :tag-type :TAG_String}, :tag-name "name"}

When we really want something like this:

    :::clojure
    {:tag-type :TAG_String, :payload "Bananrama", :tag-name "name"}

To fix this, we add a post-decoder function:

    :::clojure
    (fn [x] (merge x (:payload x)))

*get-codec* is a simple function that takes a tag-type enum value, and returns the codec for that tag:

    :::clojure get-codec
    (defn get-codec [t]
      (t {:TAG_End        (compile-frame [:error :ErrorNoFnForEnd]) ; this should never be called
          :TAG_Byte       tag-byte
          :TAG_Short      tag-short
          :TAG_Int        tag-int
          :TAG_Long       tag-long
          :TAG_Float      tag-float
          :TAG_Double     tag-double
          :TAG_Byte_Array tag-byte-array
          :TAG_String     tag-string
          :TAG_List       tag-list
          :TAG_Compound   tag-compound
          :TAG_Int_Array  tag-int-array}))

In Clojure keywords act as a function for a hash-map containing them, so this function simply looks up the map and returns the desired codec.


Array codecs
------------

A newer type of codec added is a variable length array of values.
In NBT this comes in the form of TAG_Byte_Array and TAG_Int_Array.
Both are prefixed with an int (4 bytes / 32 bits) which define how many items are in them (how many bytes, or ints).

To handle this, we turn to the Gloss codec *repeated*, which does exactly what we want, it takes a prefixed count, and then runs the supplied codec for that many iterations.

    :::clojure TAG_Byte_Array & TAG_Int_Array codecs 
    (defcodec tag-byte-array
      (ordered-map :tag-type    :TAG_Byte_Array
                   :payload (repeated :byte
                                      :prefix :int32-be)))

    (defcodec tag-int-array
      (ordered-map :tag-type    :TAG_Int_Array
                   :payload (repeated :int32-be
                                      :prefix :int32-be)))

In these examples, the first parameter is the codec to be repeated and the second is the prefix codec defining the length of the array.
Here the codecs are primatives, but as you will see shortly, they can be arbitrarily complex.


TAG\_List and dynamic codec selection
------------------------------------

An NBT TAG_List is defined as a list of objects that are all of the same tag, and are nameless.
As all objects in the list are the same, their tag-id doesn't need to be repeated, and is instead prefixed to the list.

So the binary layout is:

    [List tag-id][list name string][children id][object count][...taggless, nameless objects...]

We know how to read the first two parts, but we need to select the right codec for the children.
This is handled by the *header* codec.

*header* takes three parameters, a codec that defines the following data (the children id in our case), a function that takes the result of the codec and returns a codec to decode the body, and a third function that takes the data to encode and returns a codec to encode it with.

In the case of TAG_List, we need to combine the header codec and the repeated codec.

    :::clojure TAG_List codec
    (defcodec tag-list
      (ordered-map :tag-type  :TAG_List
                   :payload (header tag-type ;tag-type is a frame which maps a byte to an enum name
                                    (fn [t] ;returns a repeated codec of the right length
                                      (compile-frame
                                        (repeated (get-codec t)
                                                  :prefix :int32-be)))
                                    :tag-type)))

There is a lot about this codec that should seem familiar.
The tag-type is just a constant so we can identify the data type later in clojure (and in the future to know how to encode it again), and we have already seen how *repeated* and *get-codec* work.

The only thing new is *header* which we have already started to cover.
In the tag-list codec, we use header to determine the child element type of the list, and then we use an anonymous function to build up a repeated frame for the detected codec and the count of objects.

At this point you might be wondering where we read the list's tag-id and its name.
Well list is like any other tag in NBT, and it can be a nameless & tagless child of a list, so those things are determined by its parent tag, which brings us to the final tag that is the root of any NBT structure...


TAG\_Compound & the root object
------------------------------

TAG\_Compound is unique in a few different ways.
To begin with, it is the only tag that can be a root object in NBT, but it can also hold an arbirtary collection of other objects.
Finally, it is also not determined by a prefixed count as were the arrays and the list.

Instead, TAG\_Compound uses a terminating byte of 0x00 to signal it is complete.

This causes some problems with Gloss, as it doesn't seem to have a mechanism to handle this situation.
Digging through the code, there is an undocumented "wrap-delimited-sequence" that sounds like it would work for this job, but it is unable to handle this specific case.

I plan to cover Gloss in more detail in another post, so for now you will just have to take my word for it (or better yet, correct me!) and we will work through the solution.

    :::clojure tag-compound
    (defcodec tag-compound
      (ordered-map :tag-type    :TAG_Compound
                   :payload (terminated-repeat 0x00
                              (header tag-type
                                      get-named-codec
                                      :tag-type))))

Following on from tag-list, there should only be one thing that stands out, and that is the "terminated-repeat" codec.

*terminated-repeat* is not a part of Gloss, and is instead our first custom codec. What is about to follow is not pretty, and is far from complete, but it fits the requirements and allows us to read compound tags!

    :::clojure The custom terminated-repeat codec
    ;Future plans include having it terminate on an arbitrary delimiter length
    ;and to support encoding (writing)
    (defn terminated-repeat [delimiter-byte codec]
      "A gloss codec that repeats a sub-codec until a terminating byte is read.
       This only handles a terminating byte, and can only perform reads at the moment"

      (reify
        Reader
        (read-bytes [_ buf-seq]
          (let [byte-codec (compile-frame :byte)]
            (loop [results [] 
                   bufs buf-seq]
              (let [[found x bytes] (read-bytes byte-codec (take-bytes
                                                             (dup-bytes bufs)
                                                             1))]
                (if (or
                      (and found (== x delimiter-byte))
                      (== 0 (byte-count bufs)))
                  [true results (drop-bytes bufs 1)]
                  (let [[success x b] (read-bytes codec bufs)]
                    (if success
                      (recur (conj results x) b)
                      [false nil nil])))))))  ; This is incorrect right now
        Writer
        (sizeof[_]
          nil)
        (write-bytes [_ buf val]
          (throw (Exception. "write-bytes not supported")))))

Lets get the flaws out of the way first:
- It doesn't support writing data yet
- It doesn't handle incomplete streaming data like the rest of Gloss' codecs
- It is only designed for a single byte codec terminator

I plan to add the writing side of things when I need it, and when I have more experience with that side of Gloss.
The second point refers to the line with the comment "This is incorrect right now".
When a Gloss codec completes successfully, it returns a vector of [true values remaining].
When it fails due to insufficient data for the codec, it returns [false continuation data].
By doing this, when processing streaming data, Gloss knows where to resume from, and if it is not streaming data, it can raise an error regarding insufficient bytes.

I hope to get that working at some point, and I don't think it would be too difficult, but it will be a problem of having something to test against.

The final flaw, being limited to a single byte codec, was a choice to keep the task simple, and as this is the only use case in NBT, I didn't see a reason to spend time on making it more general.
This could change in the future if a need for it was found.


Now that I have gotten that out of the way, a brief explaination of how this codec works.
To start with it makes a copy of the byte-buffers, and takes a single byte.
It compares this against the terminator, and if it matches, ir returns what it has so far.
If it doesn't, it uses the child codec on the data once, and recurs on itself.


Looking back at tag-compound, you will notice that the codec given is a *header*, so each child can be different, and is determined and processed based on their type-id.


The root of it all
------------------

So if you have been paying attention, you might have noticed that tag-compound is also missing its tag-id and name.
As with a list, it can also be a child of a list or compound, so its name may not be needed and its tag-id would be consumed by its parent's *header* codec.

To end the infinite regress, we have one final codec:

    :::clojure The root codec
    (defcodec root (header tag-type
                           get-named-codec
                           :tag-type))

By now this should be pretty clear.
It will always return a tag-compound, and we could have hardcoded that in, I just thought this looked cleaner.


Conclusion
----------

This wraps up the series of reading Minecraft NBT data, I plan to cover writing NBT data in future posts.
I also have plans on diving into how Gloss works, as I learned a lot by digging through the source and working out how to make my own codec.


If you see any mistakes, please clone the blog post (it is on GitHub), make the changes and send me a pull request.
If you have suggestions on how I could improve, or if I didn't make something clear, raise an issue and I will do my best to answer it.
