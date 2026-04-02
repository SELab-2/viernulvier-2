import type { Production } from '../types/Productions'
import type { Tag } from '../types/Tags'
import { getProductions } from '../services/productions/Productions'

/**
 * This file contains utility functions related to productions.
 * Extra functions that are not directly related to API calls for productions can be added here.
 */

const RELATED_PRODUCTIONS_PAGE_SIZE = 100

/**
 * Fetches all productions that are tagged with the given tag ID, handling pagination automatically.
 *
 * @param tagId the ID of the tag for which to fetch productions
 * @returns a list of productions that contain the given tag
 */
export async function getProductionsForTag(tagId: number): Promise<Production[]> {
  const productions: Production[] = []
  let page = 1

  let response

  do {
    response = await getProductions({
      filters: { tag: tagId },
      page,
      pageSize: RELATED_PRODUCTIONS_PAGE_SIZE,
    })

    productions.push(...response.results)

    page += 1
  } while (response.next)

  return productions
}

/**
 * Fetches all productions that are tagged with any of the given tag IDs, handling pagination automatically.
 *
 * @param tags the Tag objects for which to fetch productions
 * @param lang language code used to pick a display name for each tag (falls back to `display_name` or tag id)
 * @param currentProductionId optional ID of the production to exclude from results
 * @returns an array of tuples where the first item is the tag display name and the second item is the list of productions for that tag
 */
export async function getRelatedProductions(
  tags: Tag[],
  lang: string,
  currentProductionId?: number,
): Promise<Array<[string, Production[]]>> {
  if (!tags || tags.length === 0) {
    return []
  }

  // Fetch productions for each tag in parallel.
  const perTagResults = await Promise.all(tags.map((tag) => getProductionsForTag(tag.id)))
  const result: Array<[string, Production[]]> = []

  // For each tag, we want to extract a human friendly display name
  tags.forEach((tag, idx) => {
    const list = perTagResults[idx] ?? []

    // exclude the current production
    const filtered = list.filter((p) => !(currentProductionId && p.id === currentProductionId))

    // Resolve a human-friendly name for the tag in the requested language.
    const display = (tag.name && tag.name[lang]) ?? tag.display_name ?? `tag:${tag.id}`

    result.push([display, filtered])
  })

  return result
}
