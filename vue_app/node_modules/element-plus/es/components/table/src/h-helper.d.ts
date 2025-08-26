import type { TableColumnCtx } from './table-column/defaults';
import type { DefaultRow } from './table/defaults';
type Props = {
    tableLayout: 'fixed' | 'auto';
    columns?: TableColumnCtx<DefaultRow>[];
};
export declare function hColgroup(props: Props): import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
    [key: string]: any;
}>;
export declare namespace hColgroup {
    var props: string[];
}
export {};
