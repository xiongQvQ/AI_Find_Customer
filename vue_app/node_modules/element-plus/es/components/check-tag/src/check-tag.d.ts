import type CheckTag from './check-tag.vue';
import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
export declare const checkTagProps: {
    readonly checked: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown, "primary", boolean>;
};
export type CheckTagProps = ExtractPropTypes<typeof checkTagProps>;
export type CheckTagPropsPublic = __ExtractPublicPropTypes<typeof checkTagProps>;
export declare const checkTagEmits: {
    'update:checked': (value: boolean) => boolean;
    change: (value: boolean) => boolean;
};
export type CheckTagEmits = typeof checkTagEmits;
export type CheckTagInstance = InstanceType<typeof CheckTag> & unknown;
