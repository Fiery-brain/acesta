import { mount } from '@vue/test-utils'
import DashboardFooter from '~/components/dashboard/DashboardFooter.vue'

describe('DashboardFooter', () => {
    test('is a Vue instance', () => {
        const wrapper = mount(
            DashboardFooter, {
                stubs: {
                    NuxtLink: true,
                },
            })
        expect(wrapper.vm).toBeTruthy()
    })
})
