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
 * @param currentProductionId optional ID of the production to exclude from results
 * @returns an array of tuples where the first item is the original tag object and the second item is the list of productions for that tag
 */
export async function getRelatedProductions(
  tags: Tag[],
  currentProductionId?: number,
): Promise<Array<[Tag, Production[]]>> {
  if (!tags || tags.length === 0) {
    return []
  }

  // Fetch productions for each tag in parallel.
  const perTagResults = await Promise.all(tags.map((tag) => getProductionsForTag(tag.id)))
  const result: Array<[Tag, Production[]]> = []

  // Pair every tag with its filtered production list.
  tags.forEach((tag, idx) => {
    const list = perTagResults[idx] ?? []

    // exclude the current production
    const filtered = list.filter((p) => !(currentProductionId && p.id === currentProductionId))

    result.push([tag, filtered])
  })

  return result
}
