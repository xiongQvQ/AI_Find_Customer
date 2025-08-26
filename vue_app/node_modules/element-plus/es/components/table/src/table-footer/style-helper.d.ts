import type { TableColumnCtx } from '../table-column/defaults';
import type { DefaultRow } from '../table/defaults';
import type { TableFooter } from '.';
declare function useStyle<T extends DefaultRow>(props: TableFooter<T>): {
    getCellClasses: (columns: TableColumnCtx<T>[], cellIndex: number) => string[];
    getCellStyles: (column: TableColumnCtx<T>, cellIndex: number) => import("vue").CSSProperties | undefined;
    columns: import("vue").ComputedRef<TableColumnCtx<DefaultRow>[]>;
};
export default useStyle;
