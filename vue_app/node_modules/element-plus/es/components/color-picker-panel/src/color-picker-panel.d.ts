import type { ComputedRef, ExtractPropTypes, InjectionKey, __ExtractPublicPropTypes } from 'vue';
import type ColorPickerPanel from './color-picker-panel.vue';
import type Color from './utils/color';
export declare const colorPickerPanelProps: {
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string) | (() => string | null) | ((new (...args: any[]) => string) | (() => string | null))[], unknown, unknown, undefined, boolean>;
    readonly border: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showAlpha: BooleanConstructor;
    readonly colorFormat: StringConstructor;
    readonly disabled: BooleanConstructor;
    readonly predefine: {
        readonly type: import("vue").PropType<string[]>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
};
export declare const colorPickerPanelEmits: {
    "update:modelValue": (val: string | null) => boolean;
};
export type ColorPickerPanelProps = ExtractPropTypes<typeof colorPickerPanelProps>;
export type ColorPickerPanelPropsPublic = __ExtractPublicPropTypes<typeof colorPickerPanelProps>;
export type ColorPickerPanelEmits = typeof colorPickerPanelEmits;
export type ColorPickerPanelInstance = InstanceType<typeof ColorPickerPanel> & unknown;
export interface ColorPickerPanelContext {
    currentColor: ComputedRef<string>;
}
export interface CommonColorContext {
    color: Color;
}
export declare const ROOT_COMMON_COLOR_INJECTION_KEY: InjectionKey<CommonColorContext>;
export declare const colorPickerPanelContextKey: InjectionKey<ColorPickerPanelContext>;
