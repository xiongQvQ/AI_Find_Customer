import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type UploadDragger from './upload-dragger.vue';
export declare const uploadDraggerProps: {
    readonly disabled: BooleanConstructor;
};
export type UploadDraggerProps = ExtractPropTypes<typeof uploadDraggerProps>;
export type UploadDraggerPropsPublic = __ExtractPublicPropTypes<typeof uploadDraggerProps>;
export declare const uploadDraggerEmits: {
    file: (file: File[]) => boolean;
};
export type UploadDraggerEmits = typeof uploadDraggerEmits;
export type UploadDraggerInstance = InstanceType<typeof UploadDragger> & unknown;
