// TODO check hoe filtering werkt in backend voor genres
export interface GenreFilters {
    use_as?: number;
    type?: string;
    vendor_id?: string;
    name?: string;
    external_id?: string;
}

export interface GetGenresOptions {
    page?: number;
    pageSize?: number;
    filters?: GenreFilters;
}
