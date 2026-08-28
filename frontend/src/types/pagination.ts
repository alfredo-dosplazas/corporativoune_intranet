export type PaginatedResponse<T> = {
    data: T[];
    current_page: number;
    has_next: boolean;
    has_previous: boolean;
    num_pages: number;
    next_page_number: number | null;
    previous_page_number: number | null;
};