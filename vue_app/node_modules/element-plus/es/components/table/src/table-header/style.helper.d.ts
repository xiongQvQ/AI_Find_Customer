import type { TableColumnCtx } from '../table-column/defaults';
import type { DefaultRow } from '../table/defaults';
import type { TableHeaderProps } from '.';
declare function useStyle<T extends DefaultRow>(props: TableHeaderProps<T>): {
    getHeaderRowStyle: (rowIndex: number) => any;
    getHeaderRowClass: (rowIndex: number) => string;
    getHeaderCellStyle: (rowIndex: number, columnIndex: number, row: T, column: TableColumnCtx<T>) => import("vue").CSSProperties;
    getHeaderCellClass: (rowIndex: number, columnIndex: number, row: T, column: TableColumnCtx<T>) => string;
};
export default useStyle;
