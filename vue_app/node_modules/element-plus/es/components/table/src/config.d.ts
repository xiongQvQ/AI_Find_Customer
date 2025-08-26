import type { VNode } from 'vue';
import type { TableColumnCtx } from './table-column/defaults';
import type { Store } from './store';
import type { DefaultRow, TreeNode } from './table/defaults';
export declare const cellStarts: {
    default: {
        order: string;
    };
    selection: {
        width: number;
        minWidth: number;
        realWidth: number;
        order: string;
    };
    expand: {
        width: number;
        minWidth: number;
        realWidth: number;
        order: string;
    };
    index: {
        width: number;
        minWidth: number;
        realWidth: number;
        order: string;
    };
};
export declare const getDefaultClassName: (type: string) => "table-column--selection" | "table__expand-column";
export declare const cellForced: {
    selection: {
        renderHeader<T extends DefaultRow>({ store, column, }: {
            store: Store<T>;
            column: TableColumnCtx<T>;
        }): VNode<import("vue").RendererNode, import("vue").RendererElement, {
            [key: string]: any;
        }>;
        renderCell<T extends DefaultRow>({ row, column, store, $index, }: {
            row: T;
            column: TableColumnCtx<T>;
            store: Store<T>;
            $index: number;
        }): VNode<import("vue").RendererNode, import("vue").RendererElement, {
            [key: string]: any;
        }>;
        sortable: boolean;
        resizable: boolean;
    };
    index: {
        renderHeader<T extends DefaultRow>({ column, }: {
            column: TableColumnCtx<T>;
        }): string;
        renderCell<T extends DefaultRow>({ column, $index, }: {
            column: TableColumnCtx<T>;
            $index: number;
        }): VNode<import("vue").RendererNode, import("vue").RendererElement, {
            [key: string]: any;
        }>;
        sortable: boolean;
    };
    expand: {
        renderHeader<T extends DefaultRow>({ column, }: {
            column: TableColumnCtx<T>;
        }): string;
        renderCell<T extends DefaultRow>({ column, row, store, expanded, }: {
            column: TableColumnCtx<T>;
            row: T;
            store: Store<T>;
            expanded: boolean;
        }): VNode<import("vue").RendererNode, import("vue").RendererElement, {
            [key: string]: any;
        }>;
        sortable: boolean;
        resizable: boolean;
    };
};
export declare function defaultRenderCell<T extends DefaultRow>({ row, column, $index, }: {
    row: T;
    column: TableColumnCtx<T>;
    $index: number;
}): any;
export declare function treeCellPrefix<T extends DefaultRow>({ row, treeNode, store, }: {
    row: T;
    treeNode: TreeNode;
    store: Store<T>;
}, createPlaceholder?: boolean): VNode<import("vue").RendererNode, import("vue").RendererElement, {
    [key: string]: any;
}>[] | null;
