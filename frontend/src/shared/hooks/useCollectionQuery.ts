import { useCallback, useEffect, useMemo, useRef, useState, type DependencyList } from 'react'

/**
 * Normalized error state for collection screens.
 *
 * This type is used to represent errors in a UI-safe format:
 * - `message`: optional backend or technical message to display directly
 * - `showFallback`: if true, the UI should display a generic translated fallback message instead
 */
export type CollectionErrorState = {
  message: string | null
  showFallback: boolean
}

/**
 * Floating alert state used for transient error/info messages.
 *
 * Typically rendered in a global or page-level alert component.
 * - `isOpen`: controls visibility
 * - `message`: optional message to display
 * - `close`: callback to dismiss the alert
 */
export type CollectionFloatingAlertState = {
  isOpen: boolean
  message: string | null
  close: () => void
}

/**
 * Result returned by {@link useCollectionQuery}.
 *
 * This represents the full state of a collection request:
 * - loading state
 * - fetched items + total count
 * - error handling
 * - retry capability
 * - floating alert state
 */
type CollectionQueryResult<T> = {
  /** True while the request is in-flight */
  isLoading: boolean

  /** Normalized list of items for rendering */
  items: T[]

  /** Total number of items (useful for pagination) */
  count: number

  /** Structured error state for UI rendering */
  error: CollectionErrorState

  /** Floating alert state for transient messages */
  floatingAlert: CollectionFloatingAlertState

  /** Retry the last failed request */
  retry: () => void
}

/**
 * Configuration options for {@link useCollectionQuery}.
 *
 * This hook is designed to abstract API fetching logic for collection pages.
 */
type CollectionQueryOptions<TItem, TResponse> = {
  /**
   * Dependency array that controls when the query is re-executed.
   * Works similarly to React's useEffect dependency array.
   */
  deps: DependencyList

  /**
   * Async function that fetches the raw API response.
   */
  fetcher: () => Promise<TResponse>

  /**
   * Maps raw API response to UI-ready data:
   * - `items`: list of items
   * - `count`: total item count
   */
  select: (response: TResponse) => { items: TItem[]; count: number }

  /**
   * Optional mapper to convert thrown errors into UI-safe error state.
   */
  mapError?: (error: unknown) => CollectionErrorState

  /**
   * Optional mapper to extract a floating alert message from errors.
   */
  mapFloatingMessage?: (error: unknown) => string | null

  /** Initial items before first fetch completes */
  initialItems?: TItem[]

  /** Initial total count before first fetch completes */
  initialCount?: number
}

/** Default error state when nothing has gone wrong yet. */
const DEFAULT_ERROR_STATE: CollectionErrorState = {
  message: null,
  showFallback: false,
}

/**
 * Default selector for simple array responses.
 * Assumes response is already an array.
 */
const DEFAULT_SELECT = <TItem>(items: TItem[]) => ({
  items,
  count: items.length,
})

/**
 * Default error mapping.
 * Always triggers fallback UI (generic translated message).
 */
const defaultMapError = (): CollectionErrorState => ({
  message: null,
  showFallback: true,
})

/**
 * useCollectionQuery
 *
 * A reusable data-fetching hook for collection/list pages.
 *
 * It provides:
 * - automatic loading state handling
 * - typed item + count extraction
 * - consistent error normalization
 * - retry mechanism
 * - optional floating alert integration
 *
 * @template TItem - The type of items displayed in the UI
 * @template TResponse - The raw API response type
 *
 * @param options - Configuration for fetching and transforming data
 *
 * @returns Fully normalized collection state for UI rendering
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

  const requestDepsKey = JSON.stringify(deps)

  const [isLoading, setIsLoading] = useState(true)
  const [items, setItems] = useState<TItem[]>(initialItems)
  const [count, setCount] = useState(initialCount)
  const [error, setError] = useState<CollectionErrorState>(DEFAULT_ERROR_STATE)
  const [floatingMessage, setFloatingMessage] = useState<string | null>(null)
  const [floatingOpen, setFloatingOpen] = useState(false)
  const [retryKey, setRetryKey] = useState(0)

  // Refs keep latest callbacks without retriggering effects
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

  /**
   * Retry the last failed request.
   *
   * Clears floating alert state and triggers a re-fetch.
   */
  const retry = useCallback(() => {
    setFloatingOpen(false)
    setFloatingMessage(null)
    setRetryKey((value) => value + 1)
  }, [])

  useEffect(() => {
    let isActive = true

    /**
     * Executes the API request and updates state safely.
     * Guards against state updates after unmount.
     */
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
  }, [requestDepsKey, retryKey])

  /**
   * Floating alert state derived from internal error handling.
   */
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
