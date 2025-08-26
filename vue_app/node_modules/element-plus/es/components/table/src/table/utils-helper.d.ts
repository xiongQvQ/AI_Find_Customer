import type { Store } from '../store';
import type { DefaultRow } from './defaults';
declare function useUtils<T extends DefaultRow>(store: Store<T>): {
    setCurrentRow: (row: T) => void;
    getSelectionRows: () => T[];
    toggleRowSelection: (row: T, selected?: boolean, ignoreSelectable?: boolean) => void;
    clearSelection: () => void;
    clearFilter: (columnKeys?: string[] | string) => void;
    toggleAllSelection: () => void;
    toggleRowExpansion: (row: T, expanded?: boolean) => void;
    clearSort: () => void;
    sort: (prop: string, order: string) => void;
    updateKeyChildren: (key: string, data: T[]) => void;
};
export default useUtils;
