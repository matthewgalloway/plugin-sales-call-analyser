import { createRouter, createWebHistory } from 'vue-router'
import { inIframe } from '@/common/utils'
import { useAnalysisStore } from '@/stores/analysisStore'

import UploadView from '../views/UploadView.vue'

function getBase() {
  if (inIframe()) {
    const pathName = window.location.pathname
    if (pathName.includes('/dip/')) {
      // in iframe in dataiku
      return '/dip/api/webapps/view'
    } else {
      // in iframe not in dataiku
      return pathName
    }
  } else {
    // outside iframe
    let location = window.location.pathname.match(
      /(\/public-webapps\/[a-zA-Z0-9\-_]*\/[a-zA-Z0-9\-_]*).*/,
    )
    if (location) {
      // as public-webapp
      return location[1]
    } else {
      // check as webapp
      location = window.location.pathname.match(
        /(\/webapps\/[a-zA-Z0-9\-_]*\/[a-zA-Z0-9\-_]*).*/,
      )
    }
    // either webapp or no path
    return location ? location[1] : ''
  }
}

const router = createRouter({
  history: createWebHistory(getBase()),
  routes: [
    {
      path: '/',
      redirect: '/upload',
    },
    {
      path: '/upload',
      name: 'upload',
      component: UploadView,
    },
    {
      path: '/three-whys',
      name: 'three-whys',
      component: () => import('../views/ThreeWhysView.vue'),
    },
    {
      path: '/business',
      name: 'business',
      component: () => import('../views/BusinessView.vue'),
    },
    {
      path: '/meddic',
      name: 'meddic',
      component: () => import('../views/MeddicView.vue'),
    },
    {
      path: '/deal-review',
      name: 'deal-review',
      component: () => import('../views/DealReviewView.vue'),
    },
  ],
})

// Sync router with store tab state
router.beforeEach((to, from, next) => {
  const analysisStore = useAnalysisStore()

  // Update store tab based on route
  if (to.name && typeof to.name === 'string') {
    analysisStore.setTab(to.name as any)
  }

  next()
})

export default router
