import { mount } from '@vue/test-utils'
import LandingNavigation from '~/components/LandingNavigation.vue'

describe('LandingNavigation', () => {
    test('is a Vue instance', () => {
        const wrapper = mount(
            LandingNavigation, {
                stubs: {
                    NuxtLink: true,
                },
            })
        expect(wrapper.vm).toBeTruthy()
    })
})