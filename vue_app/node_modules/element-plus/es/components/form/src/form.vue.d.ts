import type { Arrayable } from 'element-plus/es/utils';
import type { FormItemContext, FormValidateCallback, FormValidationResult } from './types';
import type { FormItemProp } from './form-item';
declare function __VLS_template(): {
    default?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly model: ObjectConstructor;
    readonly rules: {
        readonly type: import("vue").PropType<Partial<Record<string, Arrayable<import("./types").FormItemRule>>>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly labelPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "top" | "left" | "right", unknown, "right", boolean>;
    readonly requireAsteriskPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "left" | "right", unknown, "left", boolean>;
    readonly labelWidth: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly labelSuffix: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly inline: BooleanConstructor;
    readonly inlineMessage: BooleanConstructor;
    readonly statusIcon: BooleanConstructor;
    readonly showMessage: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly validateOnRuleChange: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly hideRequiredAsterisk: BooleanConstructor;
    readonly scrollToError: BooleanConstructor;
    readonly scrollIntoViewOptions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions) | ((new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions))[], unknown, unknown, true, boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
}, {
    /**
     * @description Validate the whole form. Receives a callback or returns `Promise`.
     */
    validate: (callback?: FormValidateCallback) => FormValidationResult;
    /**
     * @description Validate specified fields.
     */
    validateField: (props?: Arrayable<FormItemProp>, callback?: FormValidateCallback) => FormValidationResult;
    /**
     * @description Reset specified fields and remove validation result.
     */
    resetFields: (props?: Arrayable<FormItemProp>) => void;
    /**
     * @description Clear validation message for specified fields.
     */
    clearValidate: (props?: Arrayable<FormItemProp>) => void;
    /**
     * @description Scroll to the specified fields.
     */
    scrollToField: (prop: FormItemProp) => void;
    /**
     * @description Get a field context.
     */
    getField: (prop: FormItemProp) => FormItemContext | undefined;
    /**
     * @description All fields context.
     */
    fields: {
        $el: HTMLDivElement | undefined;
        size: import("element-plus").ComponentSize;
        validateMessage: string;
        validateState: import("./form-item").FormItemValidateState;
        isGroup: boolean;
        labelId: string;
        inputIds: string[];
        hasLabel: boolean;
        fieldValue: any;
        propString: string;
        addInputId: (id: string) => void;
        removeInputId: (id: string) => void;
        validate: (trigger: string, callback?: FormValidateCallback) => FormValidationResult;
        resetField: () => void;
        clearValidate: () => void;
        readonly labelWidth: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
        readonly labelPosition: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "top" | "left" | "right", unknown>;
        readonly inlineMessage: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, BooleanConstructor], unknown, unknown>;
        readonly showMessage: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
        readonly label?: string | undefined;
        readonly prop?: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | string[]) | (() => FormItemProp) | ((new (...args: any[]) => string | string[]) | (() => FormItemProp))[], unknown, unknown> | undefined;
        readonly required?: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown> | undefined;
        readonly error?: string | undefined;
        readonly rules?: {
            trigger?: Arrayable<string> | undefined;
            type?: import("async-validator").RuleType | undefined;
            required?: boolean | undefined;
            pattern?: string | {
                exec: (string: string) => RegExpExecArray | null;
                test: (string: string) => boolean;
                readonly source: string;
                readonly global: boolean;
                readonly ignoreCase: boolean;
                readonly multiline: boolean;
                lastIndex: number;
                compile: (pattern: string, flags?: string) => RegExp;
                readonly flags: string;
                readonly sticky: boolean;
                readonly unicode: boolean;
                readonly dotAll: boolean;
                [Symbol.match]: (string: string) => RegExpMatchArray | null;
                [Symbol.replace]: {
                    (string: string, replaceValue: string): string;
                    (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                };
                [Symbol.search]: (string: string) => number;
                [Symbol.split]: (string: string, limit?: number) => string[];
            } | undefined;
            min?: number | undefined;
            max?: number | undefined;
            len?: number | undefined;
            enum?: Array<string | number | boolean | null | undefined> | undefined;
            whitespace?: boolean | undefined;
            fields?: Record<string, import("async-validator").Rule> | undefined;
            options?: {
                suppressWarning?: boolean | undefined;
                suppressValidatorError?: boolean | undefined;
                first?: boolean | undefined;
                firstFields?: (boolean | string[]) | undefined;
                messages?: {
                    default?: (string | ((...args: unknown[]) => string)) | undefined;
                    required?: (string | ((args_0: string | undefined) => string)) | undefined;
                    enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                    whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                    date?: {
                        format?: (string | ((...args: unknown[]) => string)) | undefined;
                        parse?: (string | ((...args: unknown[]) => string)) | undefined;
                        invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                    } | undefined;
                    types?: {
                        string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                    } | undefined;
                    string?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    number?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    array?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    pattern?: {
                        mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                    } | undefined;
                } | undefined;
                keys?: string[] | undefined;
                error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
            } | undefined;
            defaultField?: {
                type?: import("async-validator").RuleType | undefined;
                required?: boolean | undefined;
                pattern?: string | {
                    exec: (string: string) => RegExpExecArray | null;
                    test: (string: string) => boolean;
                    readonly source: string;
                    readonly global: boolean;
                    readonly ignoreCase: boolean;
                    readonly multiline: boolean;
                    lastIndex: number;
                    compile: (pattern: string, flags?: string) => RegExp;
                    readonly flags: string;
                    readonly sticky: boolean;
                    readonly unicode: boolean;
                    readonly dotAll: boolean;
                    [Symbol.match]: (string: string) => RegExpMatchArray | null;
                    [Symbol.replace]: {
                        (string: string, replaceValue: string): string;
                        (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                    };
                    [Symbol.search]: (string: string) => number;
                    [Symbol.split]: (string: string, limit?: number) => string[];
                } | undefined;
                min?: number | undefined;
                max?: number | undefined;
                len?: number | undefined;
                enum?: Array<string | number | boolean | null | undefined> | undefined;
                whitespace?: boolean | undefined;
                fields?: Record<string, import("async-validator").Rule> | undefined;
                options?: {
                    suppressWarning?: boolean | undefined;
                    suppressValidatorError?: boolean | undefined;
                    first?: boolean | undefined;
                    firstFields?: (boolean | string[]) | undefined;
                    messages?: {
                        default?: (string | ((...args: unknown[]) => string)) | undefined;
                        required?: (string | ((args_0: string | undefined) => string)) | undefined;
                        enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                        date?: {
                            format?: (string | ((...args: unknown[]) => string)) | undefined;
                            parse?: (string | ((...args: unknown[]) => string)) | undefined;
                            invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                        } | undefined;
                        types?: {
                            string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        } | undefined;
                        string?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        number?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        array?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        pattern?: {
                            mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                        } | undefined;
                    } | undefined;
                    keys?: string[] | undefined;
                    error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
                } | undefined;
                defaultField?: any | any[] | undefined;
                transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
                message?: (string | ((a?: string) => string)) | undefined;
                asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
                validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
            } | {
                type?: import("async-validator").RuleType | undefined;
                required?: boolean | undefined;
                pattern?: string | {
                    exec: (string: string) => RegExpExecArray | null;
                    test: (string: string) => boolean;
                    readonly source: string;
                    readonly global: boolean;
                    readonly ignoreCase: boolean;
                    readonly multiline: boolean;
                    lastIndex: number;
                    compile: (pattern: string, flags?: string) => RegExp;
                    readonly flags: string;
                    readonly sticky: boolean;
                    readonly unicode: boolean;
                    readonly dotAll: boolean;
                    [Symbol.match]: (string: string) => RegExpMatchArray | null;
                    [Symbol.replace]: {
                        (string: string, replaceValue: string): string;
                        (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                    };
                    [Symbol.search]: (string: string) => number;
                    [Symbol.split]: (string: string, limit?: number) => string[];
                } | undefined;
                min?: number | undefined;
                max?: number | undefined;
                len?: number | undefined;
                enum?: Array<string | number | boolean | null | undefined> | undefined;
                whitespace?: boolean | undefined;
                fields?: Record<string, import("async-validator").Rule> | undefined;
                options?: {
                    suppressWarning?: boolean | undefined;
                    suppressValidatorError?: boolean | undefined;
                    first?: boolean | undefined;
                    firstFields?: (boolean | string[]) | undefined;
                    messages?: {
                        default?: (string | ((...args: unknown[]) => string)) | undefined;
                        required?: (string | ((args_0: string | undefined) => string)) | undefined;
                        enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                        date?: {
                            format?: (string | ((...args: unknown[]) => string)) | undefined;
                            parse?: (string | ((...args: unknown[]) => string)) | undefined;
                            invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                        } | undefined;
                        types?: {
                            string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        } | undefined;
                        string?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        number?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        array?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        pattern?: {
                            mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                        } | undefined;
                    } | undefined;
                    keys?: string[] | undefined;
                    error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
                } | undefined;
                defaultField?: any | any[] | undefined;
                transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
                message?: (string | ((a?: string) => string)) | undefined;
                asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
                validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
            }[] | undefined;
            transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
            message?: (string | ((a?: string) => string)) | undefined;
            asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
            validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
        } | {
            trigger?: Arrayable<string> | undefined;
            type?: import("async-validator").RuleType | undefined;
            required?: boolean | undefined;
            pattern?: string | {
                exec: (string: string) => RegExpExecArray | null;
                test: (string: string) => boolean;
                readonly source: string;
                readonly global: boolean;
                readonly ignoreCase: boolean;
                readonly multiline: boolean;
                lastIndex: number;
                compile: (pattern: string, flags?: string) => RegExp;
                readonly flags: string;
                readonly sticky: boolean;
                readonly unicode: boolean;
                readonly dotAll: boolean;
                [Symbol.match]: (string: string) => RegExpMatchArray | null;
                [Symbol.replace]: {
                    (string: string, replaceValue: string): string;
                    (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                };
                [Symbol.search]: (string: string) => number;
                [Symbol.split]: (string: string, limit?: number) => string[];
            } | undefined;
            min?: number | undefined;
            max?: number | undefined;
            len?: number | undefined;
            enum?: Array<string | number | boolean | null | undefined> | undefined;
            whitespace?: boolean | undefined;
            fields?: Record<string, import("async-validator").Rule> | undefined;
            options?: {
                suppressWarning?: boolean | undefined;
                suppressValidatorError?: boolean | undefined;
                first?: boolean | undefined;
                firstFields?: (boolean | string[]) | undefined;
                messages?: {
                    default?: (string | ((...args: unknown[]) => string)) | undefined;
                    required?: (string | ((args_0: string | undefined) => string)) | undefined;
                    enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                    whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                    date?: {
                        format?: (string | ((...args: unknown[]) => string)) | undefined;
                        parse?: (string | ((...args: unknown[]) => string)) | undefined;
                        invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                    } | undefined;
                    types?: {
                        string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                    } | undefined;
                    string?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    number?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    array?: {
                        len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                        range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                    } | undefined;
                    pattern?: {
                        mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                    } | undefined;
                } | undefined;
                keys?: string[] | undefined;
                error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
            } | undefined;
            defaultField?: {
                type?: import("async-validator").RuleType | undefined;
                required?: boolean | undefined;
                pattern?: string | {
                    exec: (string: string) => RegExpExecArray | null;
                    test: (string: string) => boolean;
                    readonly source: string;
                    readonly global: boolean;
                    readonly ignoreCase: boolean;
                    readonly multiline: boolean;
                    lastIndex: number;
                    compile: (pattern: string, flags?: string) => RegExp;
                    readonly flags: string;
                    readonly sticky: boolean;
                    readonly unicode: boolean;
                    readonly dotAll: boolean;
                    [Symbol.match]: (string: string) => RegExpMatchArray | null;
                    [Symbol.replace]: {
                        (string: string, replaceValue: string): string;
                        (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                    };
                    [Symbol.search]: (string: string) => number;
                    [Symbol.split]: (string: string, limit?: number) => string[];
                } | undefined;
                min?: number | undefined;
                max?: number | undefined;
                len?: number | undefined;
                enum?: Array<string | number | boolean | null | undefined> | undefined;
                whitespace?: boolean | undefined;
                fields?: Record<string, import("async-validator").Rule> | undefined;
                options?: {
                    suppressWarning?: boolean | undefined;
                    suppressValidatorError?: boolean | undefined;
                    first?: boolean | undefined;
                    firstFields?: (boolean | string[]) | undefined;
                    messages?: {
                        default?: (string | ((...args: unknown[]) => string)) | undefined;
                        required?: (string | ((args_0: string | undefined) => string)) | undefined;
                        enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                        date?: {
                            format?: (string | ((...args: unknown[]) => string)) | undefined;
                            parse?: (string | ((...args: unknown[]) => string)) | undefined;
                            invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                        } | undefined;
                        types?: {
                            string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        } | undefined;
                        string?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        number?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        array?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        pattern?: {
                            mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                        } | undefined;
                    } | undefined;
                    keys?: string[] | undefined;
                    error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
                } | undefined;
                defaultField?: any | any[] | undefined;
                transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
                message?: (string | ((a?: string) => string)) | undefined;
                asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
                validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
            } | {
                type?: import("async-validator").RuleType | undefined;
                required?: boolean | undefined;
                pattern?: string | {
                    exec: (string: string) => RegExpExecArray | null;
                    test: (string: string) => boolean;
                    readonly source: string;
                    readonly global: boolean;
                    readonly ignoreCase: boolean;
                    readonly multiline: boolean;
                    lastIndex: number;
                    compile: (pattern: string, flags?: string) => RegExp;
                    readonly flags: string;
                    readonly sticky: boolean;
                    readonly unicode: boolean;
                    readonly dotAll: boolean;
                    [Symbol.match]: (string: string) => RegExpMatchArray | null;
                    [Symbol.replace]: {
                        (string: string, replaceValue: string): string;
                        (string: string, replacer: (substring: string, ...args: any[]) => string): string;
                    };
                    [Symbol.search]: (string: string) => number;
                    [Symbol.split]: (string: string, limit?: number) => string[];
                } | undefined;
                min?: number | undefined;
                max?: number | undefined;
                len?: number | undefined;
                enum?: Array<string | number | boolean | null | undefined> | undefined;
                whitespace?: boolean | undefined;
                fields?: Record<string, import("async-validator").Rule> | undefined;
                options?: {
                    suppressWarning?: boolean | undefined;
                    suppressValidatorError?: boolean | undefined;
                    first?: boolean | undefined;
                    firstFields?: (boolean | string[]) | undefined;
                    messages?: {
                        default?: (string | ((...args: unknown[]) => string)) | undefined;
                        required?: (string | ((args_0: string | undefined) => string)) | undefined;
                        enum?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        whitespace?: (string | ((args_0: string | undefined) => string)) | undefined;
                        date?: {
                            format?: (string | ((...args: unknown[]) => string)) | undefined;
                            parse?: (string | ((...args: unknown[]) => string)) | undefined;
                            invalid?: (string | ((...args: unknown[]) => string)) | undefined;
                        } | undefined;
                        types?: {
                            string?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            method?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            array?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            object?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            number?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            date?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            boolean?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            integer?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            float?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            regexp?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            email?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            url?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                            hex?: (string | ((args_0: string | undefined, args_1: string | undefined) => string)) | undefined;
                        } | undefined;
                        string?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        number?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        array?: {
                            len?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            min?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            max?: (string | ((args_0: string | undefined, args_1: number | undefined) => string)) | undefined;
                            range?: (string | ((args_0: string | undefined, args_1: number | undefined, args_2: number | undefined) => string)) | undefined;
                        } | undefined;
                        pattern?: {
                            mismatch?: (string | ((args_0: string | undefined, args_1: any, args_2: string | RegExp | undefined) => string)) | undefined;
                        } | undefined;
                    } | undefined;
                    keys?: string[] | undefined;
                    error?: ((rule: import("async-validator").InternalRuleItem, message: string) => import("async-validator").ValidateError) | undefined;
                } | undefined;
                defaultField?: any | any[] | undefined;
                transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
                message?: (string | ((a?: string) => string)) | undefined;
                asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
                validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
            }[] | undefined;
            transform?: ((value: import("async-validator").Value) => import("async-validator").Value) | undefined;
            message?: (string | ((a?: string) => string)) | undefined;
            asyncValidator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => void | Promise<void>) | undefined;
            validator?: ((rule: import("async-validator").InternalRuleItem, value: import("async-validator").Value, callback: (error?: string | Error) => void, source: import("async-validator").Values, options: import("async-validator").ValidateOption) => import("async-validator").SyncValidateResult | void) | undefined;
        }[] | undefined;
        readonly validateStatus?: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "error" | "success" | "validating", unknown> | undefined;
        readonly for?: string | undefined;
    }[];
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    validate: (prop: FormItemProp, isValid: boolean, message: string) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly model: ObjectConstructor;
    readonly rules: {
        readonly type: import("vue").PropType<Partial<Record<string, Arrayable<import("./types").FormItemRule>>>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly labelPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "top" | "left" | "right", unknown, "right", boolean>;
    readonly requireAsteriskPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "left" | "right", unknown, "left", boolean>;
    readonly labelWidth: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly labelSuffix: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly inline: BooleanConstructor;
    readonly inlineMessage: BooleanConstructor;
    readonly statusIcon: BooleanConstructor;
    readonly showMessage: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly validateOnRuleChange: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly hideRequiredAsterisk: BooleanConstructor;
    readonly scrollToError: BooleanConstructor;
    readonly scrollIntoViewOptions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions) | ((new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions))[], unknown, unknown, true, boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
}>> & {
    onValidate?: ((prop: FormItemProp, isValid: boolean, message: string) => any) | undefined;
}, {
    readonly disabled: boolean;
    readonly inline: boolean;
    readonly labelWidth: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
    readonly labelPosition: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "top" | "left" | "right", unknown>;
    readonly inlineMessage: boolean;
    readonly showMessage: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly requireAsteriskPosition: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "left" | "right", unknown>;
    readonly labelSuffix: string;
    readonly validateOnRuleChange: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly scrollIntoViewOptions: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions) | ((new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions))[], unknown, unknown>;
    readonly statusIcon: boolean;
    readonly hideRequiredAsterisk: boolean;
    readonly scrollToError: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
