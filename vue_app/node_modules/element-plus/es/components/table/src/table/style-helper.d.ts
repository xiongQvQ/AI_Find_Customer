import type { DefaultRow, RenderExpanded, Table, TableProps } from './defaults';
import type { Store } from '../store';
import type TableLayout from '../table-layout';
declare function useStyle<T extends DefaultRow>(props: TableProps<T>, layout: TableLayout<T>, store: Store<T>, table: Table<T>): {
    isHidden: import("vue").Ref<boolean>;
    renderExpanded: import("vue").Ref<RenderExpanded<T> | null>;
    setDragVisible: (visible: boolean) => void;
    isGroup: import("vue").Ref<boolean>;
    handleMouseLeave: () => void;
    handleHeaderFooterMousewheel: (_event: WheelEvent, data: any) => void;
    tableSize: import("vue").ComputedRef<"" | "small" | "default" | "large">;
    emptyBlockStyle: import("vue").ComputedRef<{
        width: string;
        height: string;
    } | undefined>;
    resizeProxyVisible: import("vue").Ref<boolean>;
    bodyWidth: import("vue").ComputedRef<string>;
    resizeState: import("vue").Ref<{
        width: null | number;
        height: null | number;
        headerHeight: null | number;
    }>;
    doLayout: () => void;
    tableBodyStyles: import("vue").ComputedRef<{
        width: string;
    }>;
    tableLayout: import("vue").ComputedRef<("fixed" | "auto") | undefined>;
    scrollbarViewStyle: {
        display: string;
        verticalAlign: string;
    };
    scrollbarStyle: import("vue").ComputedRef<{
        height: string;
        maxHeight?: undefined;
    } | {
        maxHeight: string;
        height?: undefined;
    } | {
        height?: undefined;
        maxHeight?: undefined;
    }>;
};
export default useStyle;
