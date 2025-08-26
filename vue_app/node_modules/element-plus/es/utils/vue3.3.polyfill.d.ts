import type { Prop } from 'vue';
type IfAny<T, Y, N> = 0 extends 1 & T ? Y : N;
type InferPropType<T, NullAsAny = true> = [T] extends [null] ? NullAsAny extends true ? any : null : [T] extends [{
    type: null | true;
}] ? any : [T] extends [ObjectConstructor | {
    type: ObjectConstructor;
}] ? Record<string, any> : [T] extends [BooleanConstructor | {
    type: BooleanConstructor;
}] ? boolean : [T] extends [DateConstructor | {
    type: DateConstructor;
}] ? Date : [T] extends [(infer U)[] | {
    type: (infer U)[];
}] ? U extends DateConstructor ? Date | InferPropType<U, false> : InferPropType<U, false> : [T] extends [Prop<infer V, infer D>] ? unknown extends V ? keyof V extends never ? IfAny<V, V, D> : V : V : T;
type PublicRequiredKeys<T> = {
    [K in keyof T]: T[K] extends {
        required: true;
    } ? K : never;
}[keyof T];
type PublicOptionalKeys<T> = Exclude<keyof T, PublicRequiredKeys<T>>;
declare module 'vue' {
    /**
     * Extract prop types from a runtime props options object.
     * The extracted types are **public** - i.e. the expected props that can be
     * passed to component.
     */
    type __ExtractPublicPropTypes<O> = {
        [K in keyof Pick<O, PublicRequiredKeys<O>>]: InferPropType<O[K]>;
    } & {
        [K in keyof Pick<O, PublicOptionalKeys<O>>]?: InferPropType<O[K]>;
    };
    interface GlobalComponents {
    }
}
export {};
