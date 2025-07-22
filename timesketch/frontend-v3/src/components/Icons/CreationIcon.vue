<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="width"
    :height="height"
    viewBox="0 0 22 20"
    fill="none"
    :class="class"
  >
    <path
      d="M8.57172 1.42822L10.8869 7.68461L17.1434 9.99969L10.8869 12.3148L8.57172 18.5712L6.25658 12.3148L0 9.99969L6.25658 7.68461L8.57172 1.42822Z"
      fill="url(#paint0_linear_895_931)"
    />
    <path
      d="M17.8567 0L18.8213 2.60683L21.4283 3.57144L18.8213 4.53606L17.8567 7.14289L16.8921 4.53606L14.2852 3.57144L16.8921 2.60683L17.8567 0Z"
      fill="url(#paint1_linear_895_931)"
    />
    <path
      d="M17.8567 12.8571L18.8213 15.4639L21.4283 16.4286L18.8213 17.3932L17.8567 20L16.8921 17.3932L14.2852 16.4286L16.8921 15.4639L17.8567 12.8571Z"
      fill="url(#paint2_linear_895_931)"
    />
    <defs>
      <linearGradient
        id="paint0_linear_895_931"
        x1="2.0777"
        y1="16.0837"
        x2="10.7285"
        y2="14.3546"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#439DDF" />
        <stop offset="0.524208" stop-color="#4F87ED" />
        <stop offset="0.781452" stop-color="#9476C5" />
        <stop offset="0.888252" stop-color="#BC688E" />
        <stop offset="1" stop-color="#D6645D" />
      </linearGradient>
      <linearGradient
        id="paint1_linear_895_931"
        x1="15.1509"
        y1="6.10646"
        x2="18.7554"
        y2="5.38601"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#439DDF" />
        <stop offset="0.524208" stop-color="#4F87ED" />
        <stop offset="0.781452" stop-color="#9476C5" />
        <stop offset="0.888252" stop-color="#BC688E" />
        <stop offset="1" stop-color="#D6645D" />
      </linearGradient>
      <linearGradient
        id="paint2_linear_895_931"
        x1="15.1509"
        y1="18.9636"
        x2="18.7554"
        y2="18.2431"
        gradientUnits="userSpaceOnUse"
      >
        <stop stop-color="#439DDF" />
        <stop offset="0.524208" stop-color="#4F87ED" />
        <stop offset="0.781452" stop-color="#9476C5" />
        <stop offset="0.888252" stop-color="#BC688E" />
        <stop offset="1" stop-color="#D6645D" />
      </linearGradient>
    </defs>
  </svg>
</template>

<script>
export default {
  name: 'CreationIcon',
  props: {
    width: {
      type: Number,
      default: 22,
    },
    height: {
      type: Number,
      default: 20,
    },
    class: {
      type: String,
      default: '',
    },
  },
}
</script>
