<template>
  <div class="pdf-preview-container">
    <div v-if="!pdfUrl" class="no-pdf-message">
      暂无PDF可预览
    </div>
    <iframe 
      v-else
      :src="pdfUrl" 
      class="pdf-frame"
      frameborder="0"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script setup lang="ts">
defineProps({
  pdfUrl: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.pdf-preview-container {
  width: 100%;
  height: 600px;
  border: 1px solid #eaeaea;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f5f5;
}

.pdf-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.no-pdf-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
  font-size: 16px;
}
</style>