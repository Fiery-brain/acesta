import { mount } from '@vue/test-utils'

import DashboardHeader from '~/components/dashboard/DashboardHeader.vue'

const authMock = {
    loggedIn: true,
    user: {
        regions: []
    }
};

const options = {
    propsData: {
        title: "Test",
        path: "test",
        region: true,
    },
    mocks: {
        $auth: authMock
    },
}

describe('DashboardHeader', () => {
    test('is a Vue instance', () => {
        const wrapper = mount(DashboardHeader, options)
        expect(wrapper.vm).toBeTruthy()
    })
})

// authMock.loggedIn = false
//
// describe('DashboardHeader', () => {
//     test('is a Vue instance', () => {
//         const wrapper = mount(DashboardHeader, options)
//         expect(wrapper.vm).toBeTruthy()
//     })
// })
