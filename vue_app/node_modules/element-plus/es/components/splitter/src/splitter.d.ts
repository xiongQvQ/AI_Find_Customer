import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type Splitter from './splitter.vue';
export declare const splitterProps: {
    readonly layout: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "horizontal" | "vertical", unknown, "horizontal", boolean>;
    readonly lazy: BooleanConstructor;
};
export type SplitterProps = ExtractPropTypes<typeof splitterProps>;
export type SplitterPropsPublic = __ExtractPublicPropTypes<typeof splitterProps>;
export type SplitterInstance = InstanceType<typeof Splitter> & unknown;
