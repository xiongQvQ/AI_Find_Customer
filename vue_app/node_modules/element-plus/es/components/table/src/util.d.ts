import { type ElTooltipProps } from 'element-plus/es/components/tooltip';
import type { DefaultRow, Table, TreeProps } from './table/defaults';
import type { TableColumnCtx } from './table-column/defaults';
import type { CSSProperties, VNode } from 'vue';
export type TableOverflowTooltipOptions = Partial<Pick<ElTooltipProps, 'appendTo' | 'effect' | 'enterable' | 'hideAfter' | 'offset' | 'placement' | 'popperClass' | 'popperOptions' | 'showAfter' | 'showArrow' | 'transition'>>;
export type TableOverflowTooltipFormatter<T extends DefaultRow> = (data: {
    row: T;
    column: TableColumnCtx<T>;
    cellValue: any;
}) => VNode | string;
type RemovePopperFn = (() => void) & {
    trigger?: HTMLElement;
    vm?: VNode;
};
export declare const getCell: (event: Event) => HTMLTableCellElement | null;
export declare const orderBy: <T extends DefaultRow>(array: T[], sortKey: string | null, reverse: string | number | null, sortMethod: TableColumnCtx<T>["sortMethod"] | null, sortBy: string | string[] | ((a: T, index: number, array?: T[]) => string)) => T[];
export declare const getColumnById: <T extends DefaultRow>(table: {
    columns: TableColumnCtx<T>[];
}, columnId: string) => null | TableColumnCtx<T>;
export declare const getColumnByKey: <T extends DefaultRow>(table: {
    columns: TableColumnCtx<T>[];
}, columnKey: string) => TableColumnCtx<T>;
export declare const getColumnByCell: <T extends DefaultRow>(table: {
    columns: TableColumnCtx<T>[];
}, cell: HTMLElement, namespace: string) => null | TableColumnCtx<T>;
export declare const getRowIdentity: <T extends DefaultRow>(row: T, rowKey: string | ((row: T) => string) | null) => string;
export declare const getKeysMap: <T extends DefaultRow>(array: T[], rowKey: string | null, flatten?: boolean, childrenKey?: string) => Record<PropertyKey, {
    row: T;
    index: number;
}>;
export declare function mergeOptions<T extends DefaultRow, K extends DefaultRow>(defaults: T, config: K): T & K;
export declare function parseWidth(width?: number | string): number | string;
export declare function parseMinWidth(minWidth: number | string): number | string;
export declare function parseHeight(height: number | string | null): string | number | null;
export declare function compose(...funcs: ((...args: any[]) => void)[]): (...args: any[]) => void;
export declare function toggleRowStatus<T extends DefaultRow>(statusArr: T[], row: T, newVal?: boolean, tableTreeProps?: TreeProps, selectable?: ((row: T, index: number) => boolean) | null, rowIndex?: number, rowKey?: string | null): boolean;
export declare function walkTreeNode<T extends DefaultRow>(root: T[], cb: (parent: any, children: T | T[] | null, level: number) => void, childrenKey?: string, lazyKey?: string, lazy?: boolean): void;
export declare let removePopper: RemovePopperFn | null;
export declare function createTablePopper<T extends DefaultRow>(props: TableOverflowTooltipOptions, popperContent: string, row: T, column: TableColumnCtx<T> | null, trigger: HTMLElement | null, table: Table<DefaultRow>): void;
export declare const isFixedColumn: <T extends DefaultRow>(index: number, fixed: string | boolean | undefined, store: any, realColumns?: TableColumnCtx<T>[]) => {
    direction: string;
    start: number;
    after: number;
} | {
    direction?: undefined;
    start?: undefined;
    after?: undefined;
};
export declare const getFixedColumnsClass: <T extends DefaultRow>(namespace: string, index: number, fixed: string | boolean | undefined, store: any, realColumns?: TableColumnCtx<T>[], offset?: number) => string[];
export declare const getFixedColumnOffset: <T extends DefaultRow>(index: number, fixed: string | boolean | undefined, store: any, realColumns?: TableColumnCtx<T>[]) => CSSProperties | undefined;
export declare const ensurePosition: (style: CSSProperties | undefined, key: keyof CSSProperties) => void;
export {};
