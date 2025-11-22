import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: 'http://localhost:8000/api',
    prepareHeaders: (headers, { getState }) => {
      const token = getState().auth.token
      if (token) {
        headers.set('authorization', `Bearer ${token}`)
        console.log('Authorization header set with token:', token.substring(0, 20) + '...')
      } else {
        console.log('No token found in state')
      }
      return headers
    },
  }),
  tagTypes: ['User', 'Photo', 'Frame', 'Order', 'GeneratedImage'],
  endpoints: (builder) => ({
     checkAuth: builder.query({
      query: () => '/auth/check-auth',
      providesTags: ['User'],
    }),
    login: builder.mutation({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User'],
    }),
    register: builder.mutation({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),
    logout: builder.mutation({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),
    getProfile: builder.query({
      query: () => '/auth/profile',
      providesTags: ['User'],
    }),
    updateProfile: builder.mutation({
      query: (profileData) => ({
        url: '/auth/profile',
        method: 'PUT',
        body: profileData,
      }),
      invalidatesTags: ['User'],
    }),

    uploadPhoto: builder.mutation({
      query: (formData) => ({
        url: '/photos/upload',
        method: 'POST',
        body: formData,
        // Не устанавливаем Content-Type вручную для FormData
      }),
      invalidatesTags: ['Photo'],
    }),
    getUserPhotos: builder.query({
      query: () => '/photos/',
      providesTags: ['Photo'],
    }),
    getPhoto: builder.query({
      query: (photoId) => `/photos/${photoId}`,
      providesTags: ['Photo'],
    }),
    deletePhoto: builder.mutation({
      query: (photoId) => ({
        url: `/photos/${photoId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Photo'],
    }),


    getFrames: builder.query({
      query: (params = {}) => {
        const { skip = 0, limit = 100, frame_type, is_premium } = params;
        const queryParams = new URLSearchParams();
        
        if (skip) queryParams.append('skip', skip);
        if (limit) queryParams.append('limit', limit);
        if (frame_type) queryParams.append('frame_type', frame_type);
        if (is_premium !== undefined) queryParams.append('is_premium', is_premium);
        
        return `/frames?${queryParams.toString()}`;
      },
      providesTags: ['Frame'],
    }),

    // Публичный эндпоинт для рамок (без аутентификации)
    getPublicFrames: builder.query({
      query: (params = {}) => {
        const { skip = 0, limit = 100 } = params;
        const queryParams = new URLSearchParams();
        
        if (skip) queryParams.append('skip', skip);
        if (limit) queryParams.append('limit', limit);
        
        return `/frames/public?${queryParams.toString()}`;
      },
      providesTags: ['Frame'],
    }),

    selectFrame: builder.mutation({
      query: (frameId) => ({
        url: `/frames/${frameId}/select`,
        method: 'POST',
      }),
      invalidatesTags: ['Frame'],
    }),

    submitQuestionnaire: builder.mutation({
      query: (questionnaireData) => ({
        url: '/questionnaire',
        method: 'POST',
        body: questionnaireData,
      }),
      invalidatesTags: ['Questionnaire'],
    }),

    getQuestionnaire: builder.query({
      query: (questionnaireId) => `/questionnaire/${questionnaireId}`,
      providesTags: ['Questionnaire'],
    }),

    getAIPrompt: builder.query({
      query: (questionnaireId) => `/questionnaire/${questionnaireId}/ai-prompt`,
      providesTags: ['Questionnaire'],
    }),

    generateImage: builder.mutation({
      query: (generationData) => ({
        url: '/generate',
        method: 'POST',
        body: generationData,
      }),
      invalidatesTags: ['GeneratedImage'],
    }),
    getGeneratedImage: builder.query({
      query: (generationId) => `/generate/${generationId}`,
      providesTags: ['GeneratedImage'],
    }),
    getGenerationStatus: builder.query({
      query: (generationId) => `/generate/${generationId}/status`,
      providesTags: ['GeneratedImage'],
    }),

    createOrder: builder.mutation({
      query: (orderData) => ({
        url: '/orders',
        method: 'POST',
        body: orderData,
      }),
      invalidatesTags: ['Order'],
    }),
    getOrders: builder.query({
      query: () => '/orders',
      providesTags: ['Order'],
    }),
    getOrder: builder.query({
      query: (orderId) => `/orders/${orderId}`,
      providesTags: ['Order'],
    }),
    cancelOrder: builder.mutation({
      query: (orderId) => ({
        url: `/orders/${orderId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: ['Order'],
    }),

    getSubscription: builder.query({
      query: () => '/subscription',
      providesTags: ['User'],
    }),
    createSubscription: builder.mutation({
      query: (subscriptionData) => ({
        url: '/subscription',
        method: 'POST',
        body: subscriptionData,
      }),
      invalidatesTags: ['User'],
    }),
    cancelSubscription: builder.mutation({
      query: () => ({
        url: '/subscription/cancel',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),
  }),
})

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useGetProfileQuery,
  useUpdateProfileMutation,

  useUploadPhotoMutation,
  useGetUserPhotosQuery,
  useGetPhotoQuery,
  useDeletePhotoMutation,

  useGetFrameQuery,
  useGetFramesQuery,
  useSelectFrameMutation,

  useGetQuestionnaireQuery,
  useGetAIPromptQuery,
  useSubmitQuestionnaireMutation,

  useGenerateImageMutation,
  useGetGeneratedImageQuery,
  useGetGenerationStatusQuery,

  useCreateOrderMutation,
  useGetOrdersQuery,
  useGetOrderQuery,
  useCancelOrderMutation,

  useGetSubscriptionQuery,
  useCreateSubscriptionMutation,
  useCancelSubscriptionMutation,
} = api