import type { TableColumnCtx } from './defaults';
declare const _default: import("vue").DefineComponent<{
    type: {
        type: StringConstructor;
        default: string;
    };
    label: StringConstructor;
    className: StringConstructor;
    labelClassName: StringConstructor;
    property: StringConstructor;
    prop: StringConstructor;
    width: {
        type: (NumberConstructor | StringConstructor)[];
        default: string;
    };
    minWidth: {
        type: (NumberConstructor | StringConstructor)[];
        default: string;
    };
    renderHeader: import("vue").PropType<TableColumnCtx<any>["renderHeader"]>;
    sortable: {
        type: (BooleanConstructor | StringConstructor)[];
        default: boolean;
    };
    sortMethod: import("vue").PropType<TableColumnCtx<any>["sortMethod"]>;
    sortBy: import("vue").PropType<TableColumnCtx<any>["sortBy"]>;
    resizable: {
        type: BooleanConstructor;
        default: boolean;
    };
    columnKey: StringConstructor;
    align: StringConstructor;
    headerAlign: StringConstructor;
    showOverflowTooltip: {
        type: import("vue").PropType<TableColumnCtx<any>["showOverflowTooltip"]>;
        default: undefined;
    };
    tooltipFormatter: import("vue").PropType<TableColumnCtx<any>["tooltipFormatter"]>;
    fixed: (BooleanConstructor | StringConstructor)[];
    formatter: import("vue").PropType<TableColumnCtx<any>["formatter"]>;
    selectable: import("vue").PropType<TableColumnCtx<any>["selectable"]>;
    reserveSelection: BooleanConstructor;
    filterMethod: import("vue").PropType<TableColumnCtx<any>["filterMethod"]>;
    filteredValue: import("vue").PropType<TableColumnCtx<any>["filteredValue"]>;
    filters: import("vue").PropType<TableColumnCtx<any>["filters"]>;
    filterPlacement: StringConstructor;
    filterMultiple: {
        type: BooleanConstructor;
        default: boolean;
    };
    filterClassName: StringConstructor;
    index: import("vue").PropType<TableColumnCtx<any>["index"]>;
    sortOrders: {
        type: import("vue").PropType<TableColumnCtx<any>["sortOrders"]>;
        default: () => (string | null)[];
        validator: (val: TableColumnCtx<any>["sortOrders"]) => boolean;
    };
}, void, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, Record<string, any>, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    type: {
        type: StringConstructor;
        default: string;
    };
    label: StringConstructor;
    className: StringConstructor;
    labelClassName: StringConstructor;
    property: StringConstructor;
    prop: StringConstructor;
    width: {
        type: (NumberConstructor | StringConstructor)[];
        default: string;
    };
    minWidth: {
        type: (NumberConstructor | StringConstructor)[];
        default: string;
    };
    renderHeader: import("vue").PropType<TableColumnCtx<any>["renderHeader"]>;
    sortable: {
        type: (BooleanConstructor | StringConstructor)[];
        default: boolean;
    };
    sortMethod: import("vue").PropType<TableColumnCtx<any>["sortMethod"]>;
    sortBy: import("vue").PropType<TableColumnCtx<any>["sortBy"]>;
    resizable: {
        type: BooleanConstructor;
        default: boolean;
    };
    columnKey: StringConstructor;
    align: StringConstructor;
    headerAlign: StringConstructor;
    showOverflowTooltip: {
        type: import("vue").PropType<TableColumnCtx<any>["showOverflowTooltip"]>;
        default: undefined;
    };
    tooltipFormatter: import("vue").PropType<TableColumnCtx<any>["tooltipFormatter"]>;
    fixed: (BooleanConstructor | StringConstructor)[];
    formatter: import("vue").PropType<TableColumnCtx<any>["formatter"]>;
    selectable: import("vue").PropType<TableColumnCtx<any>["selectable"]>;
    reserveSelection: BooleanConstructor;
    filterMethod: import("vue").PropType<TableColumnCtx<any>["filterMethod"]>;
    filteredValue: import("vue").PropType<TableColumnCtx<any>["filteredValue"]>;
    filters: import("vue").PropType<TableColumnCtx<any>["filters"]>;
    filterPlacement: StringConstructor;
    filterMultiple: {
        type: BooleanConstructor;
        default: boolean;
    };
    filterClassName: StringConstructor;
    index: import("vue").PropType<TableColumnCtx<any>["index"]>;
    sortOrders: {
        type: import("vue").PropType<TableColumnCtx<any>["sortOrders"]>;
        default: () => (string | null)[];
        validator: (val: TableColumnCtx<any>["sortOrders"]) => boolean;
    };
}>>, {
    width: string | number;
    minWidth: string | number;
    type: string;
    resizable: boolean;
    showOverflowTooltip: boolean | Partial<Pick<import("element-plus").ElTooltipProps, "offset" | "transition" | "placement" | "effect" | "showAfter" | "hideAfter" | "popperOptions" | "enterable" | "popperClass" | "appendTo" | "showArrow">> | undefined;
    sortOrders: (import("../table/defaults").TableSortOrder | null)[];
    sortable: string | boolean;
    reserveSelection: boolean;
    filterMultiple: boolean;
}>;
export default _default;
