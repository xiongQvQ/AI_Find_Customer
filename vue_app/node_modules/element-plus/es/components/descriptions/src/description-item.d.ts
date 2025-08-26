import type { ExtractPropTypes, Slot, VNode, __ExtractPublicPropTypes } from 'vue';
export declare const descriptionItemProps: {
    label: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    span: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    rowspan: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    width: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    minWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    labelWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    align: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "center" | "left" | "right", unknown, string, boolean>;
    labelAlign: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "center" | "left" | "right", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    className: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    labelClassName: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
};
declare const DescriptionItem: import("vue").DefineComponent<{
    label: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    span: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    rowspan: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    width: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    minWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    labelWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    align: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "center" | "left" | "right", unknown, string, boolean>;
    labelAlign: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "center" | "left" | "right", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    className: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    labelClassName: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
}, unknown, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, Record<string, any>, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<ExtractPropTypes<{
    label: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    span: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    rowspan: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    width: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    minWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    labelWidth: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, string, boolean>;
    align: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "center" | "left" | "right", unknown, string, boolean>;
    labelAlign: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "center" | "left" | "right", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    className: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    labelClassName: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
}>>, {
    label: string;
    span: number;
    width: import("element-plus/es/utils").EpPropMergeType<(NumberConstructor | StringConstructor)[], unknown, unknown>;
    minWidth: import("element-plus/es/utils").EpPropMergeType<(NumberConstructor | StringConstructor)[], unknown, unknown>;
    className: string;
    labelWidth: import("element-plus/es/utils").EpPropMergeType<(NumberConstructor | StringConstructor)[], unknown, unknown>;
    align: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "center" | "left" | "right", unknown>;
    rowspan: number;
    labelClassName: string;
}>;
export default DescriptionItem;
export type DescriptionItemProps = ExtractPropTypes<typeof descriptionItemProps>;
export type DescriptionItemPropsPublic = __ExtractPublicPropTypes<typeof descriptionItemProps>;
export type DescriptionItemVNode = VNode & {
    children: {
        [name: string]: Slot;
    } | null;
    props: Partial<DescriptionItemProps> | null;
};
