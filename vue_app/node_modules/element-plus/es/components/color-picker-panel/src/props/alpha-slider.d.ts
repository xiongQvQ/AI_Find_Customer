import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type Color from '../utils/color';
export declare const alphaSliderProps: {
    readonly color: {
        readonly type: import("vue").PropType<Color>;
        readonly required: true;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly vertical: BooleanConstructor;
    readonly disabled: BooleanConstructor;
};
export type AlphaSliderProps = ExtractPropTypes<typeof alphaSliderProps>;
export type AlphaSliderPropsPublic = __ExtractPublicPropTypes<typeof alphaSliderProps>;
