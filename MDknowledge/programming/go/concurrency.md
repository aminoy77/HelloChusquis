# Go concurrency

- In Go, `go f()` launches f as a goroutine; goroutines are cheap, multiplexed onto OS threads by the runtime.
- In Go, `ch := make(chan int)` creates an unbuffered channel: sends block until a receiver is ready.
- In Go, `make(chan int, N)` buffers N values; sends block only when the buffer is full.
- In Go, `ch <- v` sends and `v := <-ch` receives; `close(ch)` signals no more values will come.
- In Go, `for v := range ch` drains until close; forgetting `close` deadlocks the consumer.
- In Go, `select` waits on multiple channels, taking the first ready case; add `default:` for non-blocking checks.
- In Go, `select` with `time.After(d)` implements timeouts around channel operations.
- In Go, `sync.WaitGroup` tracks worker completion: `Add` before launch, `Done` inside, `Wait` at the join point.
- In Go, `sync.Mutex` guards shared maps and counters; hold it for the shortest span possible.
- In Go, the race detector `go test -race` finds data races in tests and should gate concurrent code.
- In Go, share memory by communicating (channels) rather than communicating by sharing memory.
- In Go, `context.Context` carries cancellation and deadlines; pass it as the first parameter and honor `<-ctx.Done()`.
- In Go, `sync.Once` runs initialization exactly once across goroutines, ideal for lazy singletons.
- In Go, `sync.Pool` recycles temporary objects to cut GC pressure in hot paths.
- In Go, worker pools bound concurrency: fixed goroutines pulling jobs from one channel.
- In Go, never copy a `sync.Mutex` or `WaitGroup` after use; pass them by pointer.
- In Go, buffered channel of size 1 plus non-blocking send builds a cheap latest-value mailbox.
- In Go, goroutine leaks come from blocked sends/receives; always pair producers with consumers or cancellation.
