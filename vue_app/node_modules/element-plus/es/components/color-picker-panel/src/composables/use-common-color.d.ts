import Color from '../utils/color';
type CommonColorProps = {
    modelValue?: string | null;
    showAlpha: boolean;
    colorFormat?: string;
};
type CommonColorEmits = (event: 'update:modelValue', ...args: any[]) => void;
export declare const useCommonColor: <P extends CommonColorProps, E extends CommonColorEmits>(props: P, emit: E) => {
    color: Color;
};
export {};
