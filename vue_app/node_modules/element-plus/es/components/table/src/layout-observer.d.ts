import type TableLayout from './table-layout';
import type { DefaultRow, Table } from './table/defaults';
declare function useLayoutObserver<T extends DefaultRow>(root: Table<T>): {
    tableLayout: TableLayout<T>;
    onColumnsChange: (layout: TableLayout<T>) => void;
    onScrollableChange: (layout: TableLayout<T>) => void;
};
export default useLayoutObserver;
