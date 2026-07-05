**Why regular databases don't work for vectors.** A normal database is great at finding exact things — "give me the user named Sarah." But vector search never asks for an exact match. It asks "which of these millions of items is _most similar_ to this one?" A regular database has no shortcut for "most similar," so it would have to compare your query against every single row, every time. Too slow. That's why special vector databases exist.

**Approximate Nearest Neighbor (ANN).** Finding the _exact_ closest matches means checking everything, which is slow. ANN is a shortcut: instead of finding the perfect closest matches, it finds _almost_ the closest ones — but way faster. You might get 99 of the true top 100 while doing a fraction of the work. Nobody notices the missing one, and you get your results instantly. This speed-for-a-tiny-bit-of-accuracy trade is the whole game.

**Flat index (exact search).** This is the "check everything" method. It compares your query to every vector and gives you the perfect answer — 100% accurate. The downside is it gets slow as your data grows. Use it when you have a small amount of data or need guaranteed-correct results.

**IVF (grouping method).** Imagine sorting all your vectors into neighborhoods first. When a search comes in, you figure out which few neighborhoods are relevant and only look inside those, ignoring the rest of the city. Much faster. You control how many neighborhoods to check: more = more accurate but slower, fewer = faster but you might miss something near the edge.

**HNSW (map method).** Think of it like a route map with express highways and local streets. You start somewhere and keep hopping to whichever connected point is closer to what you want — "friend of a friend of a friend" — until you arrive. The highways let you cross the whole map in a few jumps; the local streets let you zero in. It's very fast and very accurate, which is why most vector databases use it by default. The catch: it uses a lot of memory.

Quick way to remember the three:

- **Flat** = check everything (perfect but slow)
- **IVF** = check the right neighborhoods (fast, needs setup)
- **HNSW** = follow the map (fastest + accurate, uses more memory)

**Metadata filtering.** Usually you don't want _just_ similar items — you want "similar items _that are mine, in English, from this year_." So each vector is stored with extra labels (owner, language, date), and the search combines "find similar" with "but only ones matching these labels." The tricky part is doing both at once without slowing things down or accidentally leaving you with too few results — and handling that well is a big reason to choose one vector database over another.

The big picture: normal databases can't rank by similarity, checking everything is too slow, so we use clever shortcuts (IVF and HNSW) to find _almost_ the closest matches fast — with Flat kept around for when you need the exact answer, and metadata labels to keep results relevant.