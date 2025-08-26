import type { ComputedRef, RendererNode, Slots } from 'vue';
import type { TableColumn, TableColumnCtx } from './defaults';
import type { DefaultRow, Table } from '../table/defaults';
declare function useRender<T extends DefaultRow>(props: TableColumnCtx<T>, slots: Slots, owner: ComputedRef<Table<T>>): {
    columnId: import("vue").Ref<string>;
    realAlign: import("vue").Ref<string | null | undefined>;
    isSubColumn: import("vue").Ref<boolean>;
    realHeaderAlign: import("vue").Ref<string | null | undefined>;
    columnOrTableParent: ComputedRef<Table<T> | TableColumn<T>>;
    setColumnWidth: (column: TableColumnCtx<T>) => TableColumnCtx<T>;
    setColumnForcedProps: (column: TableColumnCtx<T>) => TableColumnCtx<T>;
    setColumnRenders: (column: TableColumnCtx<T>) => TableColumnCtx<T>;
    getPropsData: (...propsKey: string[][]) => Record<string, any>;
    getColumnElIndex: (children: T[], child: RendererNode | null) => number;
    updateColumnOrder: () => void;
};
export default useRender;
