import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { Language } from 'element-plus/es/locale';
import type { ButtonConfigContext } from 'element-plus/es/components/button';
import type { CardConfigContext } from 'element-plus/es/components/card';
import type { DialogConfigContext } from 'element-plus/es/components/dialog';
import type { MessageConfigContext } from 'element-plus/es/components/message';
import type { LinkConfigContext } from 'element-plus/es/components/link';
export type ExperimentalFeatures = {};
export declare const configProviderProps: {
    readonly emptyValues: ArrayConstructor;
    readonly valueOnClear: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null) | ((new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null))[], unknown, unknown, undefined, boolean>;
    readonly a11y: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly locale: {
        readonly type: import("vue").PropType<Language>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly button: {
        readonly type: import("vue").PropType<ButtonConfigContext>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly card: {
        readonly type: import("vue").PropType<CardConfigContext>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly dialog: {
        readonly type: import("vue").PropType<DialogConfigContext>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly link: {
        readonly type: import("vue").PropType<LinkConfigContext>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly experimentalFeatures: {
        readonly type: import("vue").PropType<ExperimentalFeatures>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly keyboardNavigation: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly message: {
        readonly type: import("vue").PropType<MessageConfigContext>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly zIndex: NumberConstructor;
    readonly namespace: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "el", boolean>;
};
export type ConfigProviderProps = ExtractPropTypes<typeof configProviderProps>;
export type ConfigProviderPropsPublic = __ExtractPublicPropTypes<typeof configProviderProps>;
