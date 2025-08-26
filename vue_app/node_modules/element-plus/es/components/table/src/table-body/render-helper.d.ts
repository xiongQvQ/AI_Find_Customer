import type { TableBodyProps } from './defaults';
import type { DefaultRow } from '../table/defaults';
declare function useRender<T extends DefaultRow>(props: Partial<TableBodyProps<T>>): {
    wrappedRowRender: (row: T, $index: number) => import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }>[] | import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }>[][];
    tooltipContent: import("vue").Ref<string>;
    tooltipTrigger: import("vue").Ref<import("vue").VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }>>;
};
export default useRender;
