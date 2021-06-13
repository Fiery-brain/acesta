export const state = () => ({
    regionCode: ''
})

export const actions = {
    setRegionCode: (context, code) => {
        context.commit('updateRegionCode', code)
    },
}

export const mutations = {
    updateRegionCode: (state, code) => {
        state.regionCode = code
    }
}

export const getters = {
    getRegionCode: state => {
        return state.regionCode
    }
}
