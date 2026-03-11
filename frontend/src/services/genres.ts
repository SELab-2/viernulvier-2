import { api } from "./api";
import type { GetGenresOptions } from "../types/genres";

export const getGenre = async (id: number) => {
    try {
        const res = await api.get(`/genres/${id}/`);
        return res.data;
    }
    catch (error) {
        console.error("Error fetching genre:", error);
        throw error;
    }
}

export const getGenres = async (options?: GetGenresOptions) => {
    const { page, pageSize, filters } = options ?? {};

    try {
        const res = await api.get("/genres/", {
            params: {
                ...(page !== undefined ? { page } : {}),
                ...(pageSize !== undefined ? { page_size: pageSize } : {}),
                ...filters,
            },
        });
        
        return res.data;
    }
    catch (error) {
        console.error("Error fetching genres:", error);
        throw error;
    }
}

// TODO: schrijf tests