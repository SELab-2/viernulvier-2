import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

/**
 * Normalized error state for collection screens.
 *
 * When `showFallback` is true, the UI should show translated fallback copy.
 * When `message` is set, it can be rendered directly (typically for ApiError).
 */
export type CollectionErrorState = {
  message: string | null
  showFallback: boolean
}

/**
 * Floating alert state that can be fed straight into the shared alert component.
 */
export type CollectionFloatingAlertState = {
  isOpen: boolean
  message: string | null
  close: () => void
}

/**
 * Result shape returned by {@link useCollectionQuery}.
 */
type CollectionQueryResult<T> = {
  isLoading: boolean
  items: T[]
  count: number
  error: CollectionErrorState
  floatingAlert: CollectionFloatingAlertState
  retry: () => void
}

/**
 * Options for {@link useCollectionQuery}.
 *
 * - `deps` control when the query should refetch (similar to useEffect deps).
 * - `fetcher` performs the async request and returns the raw response.
 * - `select` maps the response to the list items and total count.
 * - `mapError` converts any thrown error into UI-friendly error state.
 * - `mapFloatingMessage` optionally extracts a message for the floating alert.
 */
type CollectionQueryOptions<TItem, TResponse> = {
  deps: React.DependencyList
  fetcher: () => Promise<TResponse>
  select: (response: TResponse) => { items: TItem[]; count: number }
  mapError?: (error: unknown) => CollectionErrorState
  mapFloatingMessage?: (error: unknown) => string | null
  initialItems?: TItem[]
  initialCount?: number
}

/** Default empty error state. */
const DEFAULT_ERROR_STATE: CollectionErrorState = {
  message: null,
  showFallback: false,
}

/** Default selector for array responses: items = response, count = length. */
const DEFAULT_SELECT = <TItem>(items: TItem[]) => ({ items, count: items.length })

/** Default error mapping: show fallback translated copy. */
const defaultMapError = (): CollectionErrorState => ({
  message: null,
  showFallback: true,
})

/**
 * Shared list-data hook for collection pages.
 *
 * Handles the full lifecycle:
 * - loading state
 * - list items + total count
 * - normalized error state + floating alert state
 * - retry signaling
 *
 * @typeParam TItem Item type used by the UI.
 * @typeParam TResponse Raw response type returned by `fetcher`.
 */
const useCollectionQuery = <TItem, TResponse = TItem[]>(
  options: CollectionQueryOptions<TItem, TResponse>,
): CollectionQueryResult<TItem> => {
  const {
    deps,
    fetcher,
    select = DEFAULT_SELECT as (response: TResponse) => { items: TItem[]; count: number },
    mapError = defaultMapError,
    mapFloatingMessage,
    initialItems = [],
    initialCount = 0,
  } = options

  const [isLoading, setIsLoading] = useState(true)
  const [items, setItems] = useState<TItem[]>(initialItems)
  const [count, setCount] = useState(initialCount)
  const [error, setError] = useState<CollectionErrorState>(DEFAULT_ERROR_STATE)
  const [floatingMessage, setFloatingMessage] = useState<string | null>(null)
  const [floatingOpen, setFloatingOpen] = useState(false)
  const [retryKey, setRetryKey] = useState(0)

  // Store callbacks in refs to keep the effect dependency list stable.
  const fetcherRef = useRef(fetcher)
  const selectRef = useRef(select)
  const mapErrorRef = useRef(mapError)
  const mapFloatingMessageRef = useRef(mapFloatingMessage)

  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  useEffect(() => {
    selectRef.current = select
  }, [select])

  useEffect(() => {
    mapErrorRef.current = mapError
  }, [mapError])

  useEffect(() => {
    mapFloatingMessageRef.current = mapFloatingMessage
  }, [mapFloatingMessage])

  /** Retry the last request by bumping the internal retry key. */
  const retry = useCallback(() => {
    setFloatingOpen(false)
    setFloatingMessage(null)
    setRetryKey((value) => value + 1)
  }, [])

  useEffect(() => {
    let isActive = true

    const fetchData = async () => {
      setIsLoading(true)
      setError(DEFAULT_ERROR_STATE)
      setFloatingOpen(false)
      setFloatingMessage(null)

      try {
        const response = await fetcherRef.current()

        if (!isActive) {
          return
        }

        const next = selectRef.current(response)
        setItems(next.items)
        setCount(next.count)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        const mappedError = mapErrorRef.current(error)
        setError(mappedError)
        setFloatingOpen(true)
        setFloatingMessage(mapFloatingMessageRef.current?.(error) ?? null)
        setItems([])
        setCount(0)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchData()

    return () => {
      isActive = false
    }
  }, [retryKey, ...deps])

  const floatingAlert = useMemo<CollectionFloatingAlertState>(
    () => ({
      isOpen: floatingOpen,
      message: floatingMessage,
      close: () => setFloatingOpen(false),
    }),
    [floatingMessage, floatingOpen],
  )

  return {
    isLoading,
    items,
    count,
    error,
    floatingAlert,
    retry,
  }
}

export default useCollectionQuery
