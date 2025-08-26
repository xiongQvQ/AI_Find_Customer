import type { EmitFn } from 'element-plus/es/utils';
import type { TableHeaderProps } from '.';
import type { TableColumnCtx } from '../table-column/defaults';
import type { DefaultRow, TableSortOrder } from '../table/defaults';
declare function useEvent<T extends DefaultRow>(props: TableHeaderProps<T>, emit: EmitFn<string[]>): {
    handleHeaderClick: (event: Event, column: TableColumnCtx<T>) => void;
    handleHeaderContextMenu: (event: Event, column: TableColumnCtx<T>) => void;
    handleMouseDown: (event: MouseEvent, column: TableColumnCtx<T>) => void;
    handleMouseMove: (event: MouseEvent, column: TableColumnCtx<T>) => void;
    handleMouseOut: () => void;
    handleSortClick: (event: Event, column: TableColumnCtx<T>, givenOrder?: TableSortOrder | boolean) => void;
    handleFilterClick: (event: Event) => void;
};
export default useEvent;
