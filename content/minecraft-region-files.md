Title: Minecraft Region files
Author: Nathan Williams
Date: 2013-04-16 17:10
tags: Clojure, Minecraft, Region, Anvil
category: programming

Finally we start looking at actual Minecraft data files.
Today the target is the Anvil / Region file which stores all of the chunks that make up a Minecraft world.

If you are new to this series, have a look at the earlier posts covering [NBT and Gloss][NBTGloss] to catch up.

[NBTGloss]: http://nathanwilliams.github.com/2013/02/27/reading-minecraft-nbt-data-in-clojure-with-gloss "Reading Minecraft NBT data in Clojure with Gloss"

Now, on to the Anvil / Region file format.
From here on I am going to simply call it "Region" as this was the precursor to Anvil, with the [only difference][anvilregion] being the NBT structure inside and the file extension.

[anvilregion]: http://www.minecraftwiki.net/wiki/Region_file_format "Region File Format at the Minecraft Wiki"

<!-- PELICAN_END_SUMMARY -->

Preparation
-----------

The code for this blog post is on github, so you can clone the [anvil-clj] repo to follow along.
[anvil-clj]: https://github.com/NathanWilliams/anvil-clj

After cloning it you will want to change in to the project directory, grab dependancies and start a repl:

    :::bash
    lein deps
    lein repl

Since the last post I have learnt how to have the repl start in the right namespace, so you should be in the "devel" namespace, ready to go!
From here you can look at some already decoded data by inspecting "test-header" and "test-chunk".

We will cover both in more detail throught the post.


Region File
-----------

Minecraft cuts up a world into Regions and Chunks.

In an earlier version of Minecraft, Chunks were stored directly on disk, one file each.
This caused problems with the number of open files and the overhead of opening files was bogging the game down. 

Adopted from a mod, Region files were introduced.

A Region holds 32x32 Chunks, and a Chunk consists of 16x256x16 blocks.
Region files are named based on the region coordinates such as r.0.0.mca or r.-1.-9.mca

But as the Minecraft world is generated on demand, not all Chunks will exist in a region.
To accomodate this without having large empty files, the Region design is almost like a file system of its own.
Everything is aligned to 4096 bytes, there is a header to find a chunk in the file, and chunks can be moved if they are too large for their sector.

So now you have a high level overview, lets dig into specifics.

The Header
----------

A Region file starts with a 8192 byte header which is split into two ZX indexed sections.
The first is a table of contents, mapping between a ZX coordinate (in Chunk coordinates relative to this file) to a location and size in the file, and the other is a table of timestamps recording when the chunk was last written to disk.

Each table has 1024 4-byte entires, while the timestamps are simple 32-bit numbers, the locations table is split between offset and length.
The top 3 bytes (big endian) are an offset in 4KB 'sectors' and the 4th byte is the size in 4KB sectors.


Chunk Data
----------

Once you have the offset and length, you can seek in the file and find the chunk you want.
Chunks are stored compressed and can be compressed with either ZLib or GZip, although only ZLib seems to be used by the game right now.

A chunk has its own small header, 4-bytes indicating the actual length (minus the padding to the next 4096 byte boundry), and a single byte to indicate the compression type, 1 for GZip and 2 for ZLib.

When you decompress the data you end up with an NBT encoded structure which we will leave for a future post.


Code!
-----

Now that we know what we want, lets look at how we go about doing it all.

There are three namespaces in this project:

 - devel
 - world
 - region-file

The first is a little sandbox to help with repl development.
It pulls in the other two namespaces, and loads some sample data to save repetition on the repl.

The world namespace is another convenience tool, which finds the Minecraft worlds saved on your computer and loads binary files (region files) into memory.
It is not a "complete" tool, it is not smart about loading, everything goes into memory and everything is cached.
It is however useful.
While developing the region library, I found myself tweaking a Minecraft creative world (with known blocks at known coordinates), and then copying the world files to the project directory to be reread which was tedious.
The world library instead allows me to simply name the world, dimension and region X,Z to load the file.

And finaly, the focus of this post, the functions that make up the region library.
Here we define the file format in Gloss, find the chunk we want, decompress it and pass it to the nbt library we developed in earlier posts.

The rest of this post will cover only the region-file namespace, but hopefully the other two will be clear enough to understand and work with.

Reading Region files
--------------------

Compared to previous posts, this one is pretty simple.
We only have to read the file header, and individual chunks inside the file.
If you have followed this series so far, a lot of it will look familiar.


Reading the Header
------------------

Lets start backwards, from the public interface down to the inner workings.

    :::clojure read-header
    (defn read-header [data]
      "Extract the header record from a region / anvil file."
        (gio/decode file-header
            (select-bytes data 0 8192)))

read-header is a simple function, it chops out the first 8192 bytes (the file header), and asks Gloss to decode it using the "file-header" codec.
Getting the specific bytes is done by select-bytes:

    :::clojure select-bytes
    (defn select-bytes [data offset length]
      "Select a range of bytes from a byte buffer"
    (gb/take-bytes
        (gb/drop-bytes (gb/create-buf-seq data) offset)
            length))

Gloss provides a nice set of take and drop like functions for working on buffer sequences (Clojure sequences of Java Buffers).
So all we need to do is drop the bytes we don't want (0 for the header, but used for chunks), and then take the number of bytes we want from there.
This might be inefficient, it requires the entire file to be loaded into memory, and is constantly copying buffered data around, but it is simple and works for our needs.
There is room to improve this if it ever shows to be a problem, but it is better to write code in a clean and easy to understand manner first, and optimise later if it is actually a bottleneck.

So now we get to the interesting stuff, the file-header codec:

    :::clojure file-header
    (gc/defcodec file-header
      ; 4 byte location  * 1024 entries = 4096 bytes
      ; 4 byte timestamp * 1024 entries = 4096 bytes
      (gc/ordered-map
        :locations  (gc/finite-frame 4096
                      (gc/repeated location-frame :prefix :none))
        :timestamps (gc/finite-frame 4096
                      (gc/repeated :int32         :prefix :none))))

This is where Gloss really shines, you get to express the layout of the header, instead of having to think about how to actually read it.
We start with an ordered-map, and split the data into two.
Each half is defined with a finite-frame, the number of bytes (half the header's 8192), and then a repeated codec to consume those bytes.

Starting with the easy one, timestamps is simply a 32-bit signed integer.
So out of 4096 bytes, you get 1024 timestamp entries.
Nice and simple.

Locations is a little bit more work, but not much.
To keep the codec readable, it was broken out into its own "location-frame" codec:

    :::clojure location-frame
    (gc/defcodec- location-frame
      (gc/compile-frame   :int32
                          identity          ;writer transform
                          decode-location)) ;reader transform

A location is also 4 bytes long (the same 1024 entries), but those bytes are split up 3/1.
To handle this we use Gloss' compile-frame which allows us to post process the returned data with a Clojure function.
That is where decode-location comes in:

    :::clojure decode-location
    (defn- decode-location [data]
      ; 4 bytes, split 3/1
      ; Top 3 bytes are a file offset in 4K sectors
      ; Bottom byte is the size in 4K sectors
      { :offset (* 4096 (bit-shift-right data 8))
        :size   (* 4096 (bit-and data 0xFF))})

The location is made up of a file offset and length.
Both are in 4096-byte "sectors" and in the file all sectors are padded out to a 4096 byte boundry.
So all we have to do is shift the data down by a byte (8-bits) to get the top three bytes for the location and for the size we simply mask out the top three bytes using a bitwise and.

Multiplying both numbers by 4096 gives us the actual byte location and size in the file.

Before we move on to Chunks, you might have noticed the "identity" writer transform.
In the future we will be writing data back to region files, and we will need to reverse the above transformation before we write any of it to disk.
At the moment however we are only reading, so we use identity as a "no-op" function placeholder.


Reading Chunks
--------------

Now that we know where our desired chunk is, and how big it is, we can go and get it!

Once again we will go from the outside in with the read-chunk function:

    :::clojure read-chunk
    (defn read-chunk [data offset size]
      "Read a chunk and decode the NBT data inside"
      (when-not (= 0 size)
        (nbt/decode-nbt
          (gio/decode chunk-codec
                      (select-bytes data
                                    offset
                                    size)
                      false))))  ;This tells Gloss to ignore any padding in this "sector"

While a little bit bigger than read-header, there isn't much here to confuse.
We start out with a quick safety check that we aren't trying to read an empty chunk, which is helpful if you are mapping read-chunk over an entire file, as not all chunks will exist (unless ofcourse you play a lot of Minecraft!).

The first big difference is decode-nbt, which takes the resulting decompressed binary data and turns it into a readable nbt data structre using the library we created in an earlier post.

The other difference is the additional "false" parameter to decode.
As all chunks are stored in 4096-byte sectors, they are always rounded up and the sector is padded with zero.
Gloss however throws an exception if you don't consume all data, unless you pass a false to the optional "no-remainder?" parameter.

Now we get on to the core of reading a chunk, the chunk-codec:

    :::clojure chunk-codec
    (gc/defcodec chunk-codec
      ;The byte layout of a chunk in a region file
      (gc/finite-frame :int32
        (gc/compile-frame
          (gc/ordered-map
            :compression-type compression-type
            :data (gc/repeated :byte :prefix :none))
          compressor
          extractor)))


This is pretty simple, the finite-frame tells Gloss that a 32-bit integer will define the length of the following codec, and limits the data to the codec to that amount.
The inner codec takes the 1-byte compression type, and then uses repeated to consume what is left in the finite-frame as a sequence of bytes.
This, like before, is passed to a post-decoder function (extractor) which decompresses the data.

As we are only reading at the moment, the compressor is just defined as the identity function for now, as we won't be using it.
So lets look at the extractor and how it works:

    :::clojure extractor
    (defn extractor [{:keys [compression-type data]}]
      "Used as a post-decoder by the chunk codec.
      Decompresses either GZip or ZLib"
      (let [byte-stream (ByteArrayInputStream. (byte-array (count data) data))
            stream (if (= compression-type :GZip)
                     (GZIPInputStream. byte-stream)
                     (InflaterInputStream. byte-stream))]
        (loop [result []]
          (let [buf (byte-array 1024) ;We don't know how big the decompressed data will be, so we read up to 1k at a time
                len (.read stream buf)]
            (if (< len 0)
              (gio/to-byte-buffer result)
              (recur (concat result (take len (seq buf)))))))))

As this is bigger than most forms / functions we have covered so far, we will look at it in pieces.

    :::clojure Destructuring parameters
    (defn extractor [{:keys [compression-type data]}]

If you haven't seen it before, this is destructuring, and once you understand it, you will love it!
This function takes a single parameter, a map, and then pulls it apart based on its keys.
There is a lot more to destructuring than in this example, so go look into it if you haven't seen it before, it can be really help to make your code beautiful. 

If you look back at the chunk-codec, you will notice it had a ":compression-type" and ":data" keywords.
Destructuring like this gives us the value of those two keys in the map into variables of the same name.

    :::clojure Decompression
      (let [byte-stream (ByteArrayInputStream. (byte-array (count data) data))
            stream (if (= compression-type :GZip)
                     (GZIPInputStream. byte-stream)
                     (InflaterInputStream. byte-stream))]

I looked for a nice Clojure compression library, but failed to find anything.
However the Java interop isn't actually that bad.

We turn the data into a new byte-array, and wrap it in a ByteArrayInputStream, from here we check the compression type and wrap it in the appropriate decompressor.


    :::clojure Recursively reading the stream 
        (loop [result []]
          (let [buf (byte-array 1024) ;We don't know how big the decompressed data will be, so we read up to 1k at a time
                len (.read stream buf)]
            (if (< len 0)
              (gio/to-byte-buffer result)
              (recur (concat result (take len (seq buf)))))))))

The heart of it all, we read out the data at 1k chunks at a time, concat it all together and return a Gloss byte-buffer.
The 1k value is arbitrary, and other values might give better performance.

We start with a loop.
If you are coming from an imperitive background, you need to forget what you know about loops.
In an imperitive language, when you get to the bottom of the loop, control jumps back to the top like a goto.
In Clojure the "loop" is a recursion target.
Now if you call "recur" inside of it, instead of recursively calling the function, it recursevley calls the loop (with tail call optimisation, so you don't consume more stack).

Now, in reality, and likely under the covers, this is very much the same as an imperitive loop, but like most things, it is how you think about it that matters.

So we start the loop with an empty list "result".
We make a 1k byte-array and read from the stream into it, here we are relying on the internal state of the stream, but it is a small infraction against purity for the concise code that comes out.

Reading from a stream returns the number of bytes read, or -1 if you are at the end of the stream.

So finally we have the "if" condition.
When we hit the end of the stream, we return the "result", converted to a Gloss byte-buffer.
If we have data remaining however, we recursively call the loop, passing in the current "result" concatenated with the bytes we just read (trimmed of course, as a stream can, and will, return a varying number of bytes from 1 to the size of your buffer).


The only thing left that we haven't covered is the compression-type codec used in the chunk codec.

    :::clojure compression-type
    (gc/defcodec compression-type
      ;The file format and minecraft support both
      ;But so far only ZLib is actually used
      (gc/enum :byte {:GZip 1
                      :ZLib 2}))

This is pretty simple and if you have read the earlier posts you should recognise it and how it works.


Conclusion
----------

Reading a Region file is actually pretty easy.
So easy in fact that when I first attempted it I got carried away and started to decode the chunk NBT structure inside, mapping block IDs, biomes and more to their human readable names!

As always, if you see a mistake in any of the above, from grammer and spelling to coding, clone the Git repo for the blog, make the change and send me a pull request.
If you have suggestions or questions, raise an issue and I will get back to you.


Next Time
---------

I have something a bit more interesting in mind for next time to change things up a bit.
While I am having fun decoding these files, after a while it starts to become endless walls of text in the form of Clojure data structures.
I would like to do something a bit more visual next time, lets see how long it takes me to actually get there!
