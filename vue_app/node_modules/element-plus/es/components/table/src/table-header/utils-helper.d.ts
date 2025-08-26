import type { DefaultRow } from '../table/defaults';
import type { TableColumnCtx } from '../table-column/defaults';
import type { TableHeaderProps } from '.';
export declare const convertToRows: <T extends DefaultRow>(originColumns: TableColumnCtx<T>[]) => TableColumnCtx<T>[][];
declare function useUtils<T extends DefaultRow>(props: TableHeaderProps<T>): {
    isGroup: import("vue").ComputedRef<boolean>;
    toggleAllSelection: (event: Event) => void;
    columnRows: import("vue").ComputedRef<TableColumnCtx<T>[][]>;
};
export default useUtils;
