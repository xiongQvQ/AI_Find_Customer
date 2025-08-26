import type { TableColumnCtx } from '../table-column/defaults';
import type { TableBodyProps } from './defaults';
import type { DefaultRow } from '../table/defaults';
declare function useStyles<T extends DefaultRow>(props: Partial<TableBodyProps<T>>): {
    getRowStyle: (row: T, rowIndex: number) => any;
    getRowClass: (row: T, rowIndex: number) => string[];
    getCellStyle: (rowIndex: number, columnIndex: number, row: T, column: TableColumnCtx<T>) => import("vue").CSSProperties;
    getCellClass: (rowIndex: number, columnIndex: number, row: T, column: TableColumnCtx<T>, offset: number) => string;
    getSpan: (row: T, column: TableColumnCtx<T>, rowIndex: number, columnIndex: number) => {
        rowspan: number;
        colspan: number;
    };
    getColspanRealWidth: (columns: TableColumnCtx<T>[], colspan: number, index: number) => number;
};
export default useStyles;
